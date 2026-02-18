"""
Agent Module Routes
Secure routes for human agents to review complaints and generate validated solutions
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.database import get_db, get_ist_time
from app.db.models import Complaint, AgentResolution, ModelValidation, AgentAuditLog, User
from app.services.multi_model_validator import multi_model_validator
from app.services.email_service import email_service
from typing import Optional, List, Dict
import asyncio
from datetime import datetime

router = APIRouter(prefix="/agent", tags=["Agent Module"])


def verify_admin_access(user_email: str, db: Session) -> User:
    """Verify that the user is an admin or agent"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != "Admin" and not user.is_agent:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only admins and authorized agents can access this module."
        )
    
    return user


def log_agent_action(
    db: Session,
    agent_email: str,
    action: str,
    complaint_id: Optional[int] = None,
    resolution_id: Optional[int] = None,
    details: Optional[Dict] = None,
    request: Optional[Request] = None
):
    """Log all agent actions for audit trail"""
    try:
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        audit_log = AgentAuditLog(
            agent_email=agent_email,
            action=action,
            complaint_id=complaint_id,
            resolution_id=resolution_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=get_ist_time()
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"❌ Failed to log agent action: {e}")


@router.get("/complaints/queue")
async def get_complaint_queue(
    agent_email: str,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    sentiment: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Get structured queue of complaints for agent review
    
    Filters:
    - status: Pending, Under Review, Resolved
    - category: Banking, Technical, Service, etc.
    - priority: High, Medium, Low
    - sentiment: Negative, Critical, Neutral, Positive
    """
    # Verify admin/agent access
    agent = verify_admin_access(agent_email, db)
    
    # Log access
    log_agent_action(
        db, agent_email, "VIEW_COMPLAINT_QUEUE",
        details={"filters": {"status": status, "category": category, "priority": priority, "sentiment": sentiment}},
        request=request
    )
    
    # Build query
    query = db.query(Complaint)
    
    # Apply filters
    if status:
        if status == "Pending":
            query = query.filter(Complaint.is_resolved == False)
            # Exclude complaints already under agent review
            query = query.outerjoin(AgentResolution).filter(AgentResolution.id == None)
        elif status == "Under Review":
            query = query.join(AgentResolution).filter(
                AgentResolution.status.in_(["draft", "validating"])
            )
        elif status == "Resolved":
            query = query.filter(Complaint.is_resolved == True)
    
    if category:
        query = query.filter(Complaint.category == category)
    
    if priority:
        query = query.filter(Complaint.priority == priority)
    
    if sentiment:
        query = query.filter(Complaint.sentiment == sentiment)
    
    # Order by priority and timestamp (most urgent first)
    priority_order = {"High": 1, "Medium": 2, "Low": 3}
    query = query.order_by(
        desc(Complaint.created_at)  # Most recent first
    )
    
    # Get total count
    total_count = query.count()
    
    # Paginate
    complaints = query.offset(skip).limit(limit).all()
    
    # Format response
    complaint_queue = []
    for complaint in complaints:
        # Get agent resolution if exists
        agent_resolution = db.query(AgentResolution).filter(
            AgentResolution.complaint_id == complaint.id
        ).first()
        
        # Get user details
        user = db.query(User).filter(User.email == complaint.email).first()
        
        # Determine current status
        current_status = "Pending"
        if complaint.is_resolved:
            current_status = "Resolved"
        elif agent_resolution:
            current_status = "Under Review"
        
        # Calculate risk level based on sentiment and priority
        risk_level = "Low"
        if complaint.sentiment in ["Critical", "Negative"] and complaint.priority == "High":
            risk_level = "Critical"
        elif complaint.sentiment == "Critical" or complaint.priority == "High":
            risk_level = "High"
        elif complaint.priority == "Medium":
            risk_level = "Medium"
        
        complaint_queue.append({
            "id": complaint.id,
            "ticket_id": complaint.ticket_id,
            "user": {
                "name": user.full_name if user else "Unknown",
                "email": complaint.email,
                "user_id": user.id if user else None,
                "location": user.location if user else None,
                "phone": user.phone if user else None
            },
            "complaint": {
                "subject": complaint.subject,
                "description": complaint.description,
                "category": complaint.category,
                "priority": complaint.priority
            },
            "ai_analysis": {
                "sentiment": complaint.sentiment,
                "sentiment_score": complaint.sentiment_score,
                "risk_level": risk_level,
                "ai_solution": complaint.solution
            },
            "status": current_status,
            "created_at": complaint.created_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
            "agent_resolution_id": agent_resolution.id if agent_resolution else None
        })
    
    return {
        "success": True,
        "total_count": total_count,
        "returned_count": len(complaint_queue),
        "skip": skip,
        "limit": limit,
        "complaints": complaint_queue
    }


@router.get("/complaints/{complaint_id}")
async def get_complaint_details(
    complaint_id: int,
    agent_email: str,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Get detailed complaint information for deep analysis"""
    # Verify admin/agent access
    agent = verify_admin_access(agent_email, db)
    
    # Get complaint
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Log access
    log_agent_action(
        db, agent_email, "VIEW_COMPLAINT_DETAILS",
        complaint_id=complaint_id,
        request=request
    )
    
    # Get user details
    user = db.query(User).filter(User.email == complaint.email).first()
    
    # Get existing agent resolution if any
    agent_resolution = db.query(AgentResolution).filter(
        AgentResolution.complaint_id == complaint_id
    ).first()
    
    resolution_data = None
    if agent_resolution:
        # Get validation results
        validations = db.query(ModelValidation).filter(
            ModelValidation.resolution_id == agent_resolution.id
        ).all()
        
        resolution_data = {
            "id": agent_resolution.id,
            "agent_name": agent_resolution.agent_name,
            "agent_email": agent_resolution.agent_email,
            "draft_solution": agent_resolution.draft_solution,
            "final_solution": agent_resolution.final_solution,
            "confidence_score": agent_resolution.confidence_score,
            "validation_summary": agent_resolution.validation_summary,
            "status": agent_resolution.status,
            "created_at": agent_resolution.created_at.isoformat(),
            "updated_at": agent_resolution.updated_at.isoformat() if agent_resolution.updated_at else None,
            "validations": [
                {
                    "model_name": v.model_name,
                    "score": v.score,
                    "feedback": v.feedback,
                    "passed": v.passed
                }
                for v in validations
            ]
        }
    
    return {
        "success": True,
        "complaint": {
            "id": complaint.id,
            "ticket_id": complaint.ticket_id,
            "subject": complaint.subject,
            "description": complaint.description,
            "category": complaint.category,
            "priority": complaint.priority,
            "sentiment": complaint.sentiment,
            "sentiment_score": complaint.sentiment_score,
            "ai_solution": complaint.solution,
            "is_resolved": complaint.is_resolved,
            "created_at": complaint.created_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None
        },
        "user": {
            "id": user.id if user else None,
            "name": user.full_name if user else "Unknown",
            "email": complaint.email,
            "phone": user.phone if user else None,
            "location": user.location if user else None,
            "bio": user.bio if user else None
        },
        "agent_resolution": resolution_data
    }


@router.post("/resolutions/draft")
async def create_draft_resolution(
    complaint_id: int = Body(...),
    agent_email: str = Body(...),
    agent_name: str = Body(...),
    draft_solution: str = Body(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Create a draft resolution (before validation)"""
    # Verify admin/agent access
    agent = verify_admin_access(agent_email, db)
    
    # Get complaint
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Check if draft already exists
    existing_resolution = db.query(AgentResolution).filter(
        AgentResolution.complaint_id == complaint_id
    ).first()
    
    if existing_resolution:
        # Update existing draft
        existing_resolution.draft_solution = draft_solution
        existing_resolution.agent_name = agent_name
        existing_resolution.agent_email = agent_email
        existing_resolution.status = "draft"
        existing_resolution.updated_at = get_ist_time()
        db.commit()
        db.refresh(existing_resolution)
        
        log_agent_action(
            db, agent_email, "UPDATE_DRAFT_RESOLUTION",
            complaint_id=complaint_id,
            resolution_id=existing_resolution.id,
            request=request
        )
        
        return {
            "success": True,
            "message": "Draft resolution updated successfully",
            "resolution_id": existing_resolution.id
        }
    
    # Create new draft
    new_resolution = AgentResolution(
        complaint_id=complaint_id,
        agent_email=agent_email,
        agent_name=agent_name,
        draft_solution=draft_solution,
        status="draft",
        created_at=get_ist_time()
    )
    db.add(new_resolution)
    db.commit()
    db.refresh(new_resolution)
    
    log_agent_action(
        db, agent_email, "CREATE_DRAFT_RESOLUTION",
        complaint_id=complaint_id,
        resolution_id=new_resolution.id,
        request=request
    )
    
    return {
        "success": True,
        "message": "Draft resolution created successfully",
        "resolution_id": new_resolution.id
    }


@router.post("/resolutions/validate")
async def validate_resolution(
    resolution_id: int = Body(...),
    agent_email: str = Body(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Validate resolution using multi-model validation
    This runs the draft solution through 5-10 Groq models for consensus
    """
    # Verify admin/agent access
    agent = verify_admin_access(agent_email, db)
    
    # Get resolution
    resolution = db.query(AgentResolution).filter(AgentResolution.id == resolution_id).first()
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")
    
    # Get complaint
    complaint = db.query(Complaint).filter(Complaint.id == resolution.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Update status to validating
    resolution.status = "validating"
    db.commit()
    
    log_agent_action(
        db, agent_email, "START_VALIDATION",
        complaint_id=complaint.id,
        resolution_id=resolution_id,
        request=request
    )
    
    try:
        # Prepare complaint data for validation
        complaint_data = {
            "category": complaint.category,
            "priority": complaint.priority,
            "sentiment": complaint.sentiment,
            "subject": complaint.subject,
            "description": complaint.description
        }
        
        # Run multi-model validation
        print(f"🔍 Starting multi-model validation for resolution {resolution_id}...")
        validation_result = await multi_model_validator.validate_solution(
            complaint=complaint_data,
            draft_solution=resolution.draft_solution
        )
        
        # Store validation results
        resolution.confidence_score = validation_result["confidence_score"]
        resolution.validation_summary = validation_result["model_agreement"]
        
        # Store individual model validations
        for model_result in validation_result["validation_results"]:
            model_validation = ModelValidation(
                resolution_id=resolution_id,
                model_name=model_result["model"],
                score=model_result["overall_score"],
                feedback=model_result["feedback"],
                passed=model_result["passed"],
                created_at=get_ist_time()
            )
            db.add(model_validation)
        
        # Update resolution status based on approval
        approval_status = validation_result["approval_status"]
        if approval_status == "approved":
            resolution.status = "approved"
            resolution.final_solution = resolution.draft_solution
        elif approval_status == "needs_revision":
            resolution.status = "needs_revision"
        else:
            resolution.status = "rejected"
        
        resolution.updated_at = get_ist_time()
        db.commit()
        db.refresh(resolution)
        
        log_agent_action(
            db, agent_email, "VALIDATION_COMPLETE",
            complaint_id=complaint.id,
            resolution_id=resolution_id,
            details={
                "approval_status": approval_status,
                "confidence_score": validation_result["confidence_score"]
            },
            request=request
        )
        
        return {
            "success": True,
            "validation_result": {
                "approval_status": approval_status,
                "confidence_score": validation_result["confidence_score"],
                "model_agreement": validation_result["model_agreement"],
                "recommendations": validation_result["recommendations"],
                "validation_count": len(validation_result["validation_results"])
            },
            "resolution": {
                "id": resolution.id,
                "status": resolution.status,
                "confidence_score": resolution.confidence_score
            }
        }
        
    except Exception as e:
        # Update status to failed
        resolution.status = "validation_failed"
        db.commit()
        
        log_agent_action(
            db, agent_email, "VALIDATION_FAILED",
            complaint_id=complaint.id,
            resolution_id=resolution_id,
            details={"error": str(e)},
            request=request
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/resolutions/send")
async def send_resolution_to_user(
    resolution_id: int = Body(...),
    agent_email: str = Body(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Send approved resolution to user
    Only works if resolution is approved and confidence threshold is met
    """
    # Verify admin/agent access
    agent = verify_admin_access(agent_email, db)
    
    # Get resolution
    resolution = db.query(AgentResolution).filter(AgentResolution.id == resolution_id).first()
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")
    
    # Check if approved
    if resolution.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot send resolution with status '{resolution.status}'. Only approved resolutions can be sent."
        )
    
    # Check confidence threshold
    if resolution.confidence_score < 0.75:
        raise HTTPException(
            status_code=400,
            detail=f"Confidence score ({resolution.confidence_score}) is below threshold (0.75)"
        )
    
    # Get complaint
    complaint = db.query(Complaint).filter(Complaint.id == resolution.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Get user
    user = db.query(User).filter(User.email == complaint.email).first()
    
    try:
        # Send email to user
        email_service.send_agent_resolution(
            user_email=complaint.email,
            user_name=user.full_name if user else "Valued Customer",
            ticket_id=complaint.ticket_id,
            complaint_subject=complaint.subject,
            agent_solution=resolution.final_solution,
            agent_name=resolution.agent_name
        )
        
        # Mark complaint as resolved
        complaint.is_resolved = True
        complaint.updated_at = get_ist_time()
        
        # Update resolution status
        resolution.status = "sent"
        resolution.updated_at = get_ist_time()
        
        db.commit()
        
        log_agent_action(
            db, agent_email, "SEND_RESOLUTION",
            complaint_id=complaint.id,
            resolution_id=resolution_id,
            details={
                "user_email": complaint.email,
                "confidence_score": resolution.confidence_score
            },
            request=request
        )
        
        return {
            "success": True,
            "message": "Resolution sent to user successfully",
            "resolution": {
                "id": resolution.id,
                "status": resolution.status,
                "confidence_score": resolution.confidence_score,
                "sent_to": complaint.email
            }
        }
        
    except Exception as e:
        log_agent_action(
            db, agent_email, "SEND_RESOLUTION_FAILED",
            complaint_id=complaint.id,
            resolution_id=resolution_id,
            details={"error": str(e)},
            request=request
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send resolution: {str(e)}"
        )


@router.get("/resolutions")
async def get_all_resolutions(
    agent_email: str,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Get all agent resolutions for admin dashboard
    Shows complete resolution history with validation metrics
    """
    # Verify admin/agent access
    agent = verify_admin_access(agent_email, db)
    
    # Build query
    query = db.query(AgentResolution)
    
    if status:
        query = query.filter(AgentResolution.status == status)
    
    # Order by most recent first
    query = query.order_by(desc(AgentResolution.created_at))
    
    # Get total count
    total_count = query.count()
    
    # Paginate
    resolutions = query.offset(skip).limit(limit).all()
    
    # Format response
    resolution_list = []
    for resolution in resolutions:
        # Get complaint
        complaint = db.query(Complaint).filter(Complaint.id == resolution.complaint_id).first()
        
        # Get user
        user = db.query(User).filter(User.email == complaint.email).first() if complaint else None
        
        resolution_list.append({
            "id": resolution.id,
            "complaint_id": resolution.complaint_id,
            "ticket_id": complaint.ticket_id if complaint else None,
            "user": {
                "name": user.full_name if user else "Unknown",
                "email": complaint.email if complaint else None
            },
            "complaint_category": complaint.category if complaint else None,
            "sentiment": complaint.sentiment if complaint else None,
            "agent_name": resolution.agent_name,
            "agent_email": resolution.agent_email,
            "final_solution": resolution.final_solution,
            "confidence_score": resolution.confidence_score,
            "status": resolution.status,
            "created_at": resolution.created_at.isoformat(),
            "updated_at": resolution.updated_at.isoformat() if resolution.updated_at else None
        })
    
    log_agent_action(
        db, agent_email, "VIEW_ALL_RESOLUTIONS",
        details={"status_filter": status, "count": len(resolution_list)},
        request=request
    )
    
    return {
        "success": True,
        "total_count": total_count,
        "returned_count": len(resolution_list),
        "skip": skip,
        "limit": limit,
        "resolutions": resolution_list
    }


@router.get("/audit-logs")
async def get_audit_logs(
    agent_email: str,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get audit logs for agent actions (admin only)"""
    # Verify admin access
    agent = verify_admin_access(agent_email, db)
    
    # Build query
    query = db.query(AgentAuditLog)
    
    if action:
        query = query.filter(AgentAuditLog.action == action)
    
    # Order by most recent first
    query = query.order_by(desc(AgentAuditLog.timestamp))
    
    # Get total count
    total_count = query.count()
    
    # Paginate
    logs = query.offset(skip).limit(limit).all()
    
    # Format response
    audit_logs = [
        {
            "id": log.id,
            "agent_email": log.agent_email,
            "action": log.action,
            "complaint_id": log.complaint_id,
            "resolution_id": log.resolution_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "timestamp": log.timestamp.isoformat()
        }
        for log in logs
    ]
    
    return {
        "success": True,
        "total_count": total_count,
        "returned_count": len(audit_logs),
        "skip": skip,
        "limit": limit,
        "audit_logs": audit_logs
    }
