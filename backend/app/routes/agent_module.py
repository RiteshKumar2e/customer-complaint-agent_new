"""
Agent Module API Routes
Secure endpoints for human agents to review complaints and send verified solutions
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import Optional, List
from datetime import datetime
import json

from app.db.database import get_db, get_ist_time
from app.db.models import (
    User, Complaint, AgentResolution, 
    ModelValidation, AgentAuditLog
)
from app.services.multi_model_validator import multi_model_validator
from app.services.email_service import email_service

router = APIRouter(prefix="/agent", tags=["agent-module"])

# ============================================
# AUTHENTICATION & AUTHORIZATION
# ============================================

def require_agent_access(user_email: str, db: Session) -> User:
    """
    Verify that the user has agent access
    Only admins and users with is_agent=True can access
    """
    user = db.query(User).filter(User.email == user_email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.role != "Admin" and not user.is_agent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Agent role required."
        )
    
    return user

def log_agent_action(
    db: Session,
    agent_id: int,
    action: str,
    complaint_id: Optional[int] = None,
    ticket_id: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None
):
    """Log agent action to audit trail"""
    audit_log = AgentAuditLog(
        agent_id=agent_id,
        action=action,
        complaint_id=complaint_id,
        ticket_id=ticket_id,
        details=details,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        timestamp=get_ist_time()
    )
    db.add(audit_log)
    db.commit()

# ============================================
# COMPLAINT QUEUE ENDPOINTS
# ============================================

@router.get("/complaints/queue")
def get_complaint_queue(
    agent_email: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sentiment: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get structured queue of complaints for agent review
    
    Query Parameters:
    - status: pending, under_review, resolved
    - priority: High, Medium, Low
    - sentiment: Positive, Neutral, Negative, Angry
    - category: Technical, Billing, Delivery, Service, Security
    - search: Search in ticket_id, name, email, subject, description
    - sort_by: created_at, priority, sentiment
    - sort_order: asc, desc
    - page: Page number (default 1)
    - limit: Items per page (default 50)
    """
    # Verify agent access
    agent = require_agent_access(agent_email, db)
    
    # Build query
    query = db.query(Complaint)
    
    # Apply filters
    if status:
        if status == "pending":
            query = query.filter(Complaint.is_resolved == False)
        elif status == "resolved":
            query = query.filter(Complaint.is_resolved == True)
    
    if priority:
        query = query.filter(Complaint.priority == priority)
    
    if sentiment:
        query = query.filter(Complaint.sentiment == sentiment)
    
    if category:
        query = query.filter(Complaint.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Complaint.ticket_id.like(search_term),
                Complaint.name.like(search_term),
                Complaint.email.like(search_term),
                Complaint.subject.like(search_term),
                Complaint.description.like(search_term)
            )
        )
    
    # Apply sorting
    if sort_by == "priority":
        # Custom priority sorting: High > Medium > Low
        priority_order = {"High": 3, "Medium": 2, "Low": 1}
        # This is a simplified approach; for complex sorting, use CASE in SQL
        pass  # Will sort in Python after fetching
    elif sort_by == "created_at":
        if sort_order == "desc":
            query = query.order_by(desc(Complaint.created_at))
        else:
            query = query.order_by(Complaint.created_at)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    complaints = query.offset(offset).limit(limit).all()
    
    # Format response
    complaint_list = []
    for complaint in complaints:
        # Check if there's an agent resolution
        resolution = db.query(AgentResolution).filter(
            AgentResolution.complaint_id == complaint.id
        ).first()
        
        complaint_data = {
            "id": complaint.id,
            "ticket_id": complaint.ticket_id or f"#{complaint.id}",
            "user_name": complaint.name,
            "user_email": complaint.email,
            "category": complaint.category,
            "priority": complaint.priority,
            "sentiment": complaint.sentiment,
            "subject": complaint.subject,
            "description": complaint.description or complaint.complaint_text,
            "status": "resolved" if complaint.is_resolved else "pending",
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
            "agent_status": resolution.status if resolution else None,
            "agent_name": resolution.agent_name if resolution else None
        }
        complaint_list.append(complaint_data)
    
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit,
        "complaints": complaint_list
    }

@router.get("/complaints/{ticket_id}")
def get_complaint_detail(
    ticket_id: str,
    agent_email: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get detailed complaint information with full AI analysis
    """
    # Verify agent access
    agent = require_agent_access(agent_email, db)
    
    # Get complaint
    complaint = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ticket ID {ticket_id} not found"
        )
    
    # Log action
    log_agent_action(
        db, agent.id, "view_complaint",
        complaint_id=complaint.id,
        ticket_id=ticket_id,
        request=request
    )
    
    # Get agent resolution if exists
    resolution = db.query(AgentResolution).filter(
        AgentResolution.complaint_id == complaint.id
    ).first()
    
    # Format response
    return {
        "complaint": {
            "id": complaint.id,
            "ticket_id": complaint.ticket_id,
            "user_name": complaint.name,
            "user_email": complaint.email,
            "user_id": complaint.id,  # Using complaint ID as user reference
            "category": complaint.category,
            "priority": complaint.priority,
            "sentiment": complaint.sentiment,
            "subject": complaint.subject,
            "description": complaint.description or complaint.complaint_text,
            "ai_response": complaint.response,
            "ai_solution": complaint.solution,
            "ai_action": complaint.action,
            "satisfaction_prediction": complaint.satisfaction_prediction,
            "similar_complaints": complaint.similar_complaints,
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
            "is_resolved": complaint.is_resolved
        },
        "agent_resolution": {
            "id": resolution.id if resolution else None,
            "draft_solution": resolution.draft_solution if resolution else None,
            "final_solution": resolution.final_solution if resolution else None,
            "validation_status": resolution.validation_status if resolution else None,
            "confidence_score": resolution.confidence_score if resolution else None,
            "status": resolution.status if resolution else None,
            "created_at": resolution.created_at.isoformat() if resolution and resolution.created_at else None
        } if resolution else None
    }

# ============================================
# VALIDATION ENDPOINTS
# ============================================

@router.post("/validate-solution")
async def validate_solution(
    agent_email: str,
    ticket_id: str,
    draft_solution: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Validate agent's solution using multi-model validation
    
    Request Body:
    {
        "agent_email": "agent@example.com",
        "ticket_id": "QF-2025-001",
        "draft_solution": "Here is my proposed solution..."
    }
    """
    # Verify agent access
    agent = require_agent_access(agent_email, db)
    
    # Get complaint
    complaint = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ticket ID {ticket_id} not found"
        )
    
    # Prepare complaint data for validation
    complaint_data = {
        "category": complaint.category,
        "priority": complaint.priority,
        "sentiment": complaint.sentiment,
        "subject": complaint.subject,
        "description": complaint.description or complaint.complaint_text
    }
    
    # Run multi-model validation
    print(f"🔍 Starting validation for ticket {ticket_id}...")
    validation_result = await multi_model_validator.validate_solution(
        complaint_data,
        draft_solution
    )
    
    # Create or update agent resolution
    resolution = db.query(AgentResolution).filter(
        AgentResolution.complaint_id == complaint.id
    ).first()
    
    if not resolution:
        resolution = AgentResolution(
            complaint_id=complaint.id,
            ticket_id=ticket_id,
            agent_id=agent.id,
            agent_name=agent.full_name or agent.email,
            draft_solution=draft_solution,
            final_solution=draft_solution,  # Will be updated when sent
            validation_results=validation_result.get("validation_results"),
            confidence_score=validation_result.get("confidence_score"),
            validation_status=validation_result.get("approval_status"),
            model_agreement_metrics=validation_result.get("model_agreement"),
            status="validated" if validation_result.get("approval_status") == "approved" else "draft"
        )
        db.add(resolution)
    else:
        resolution.draft_solution = draft_solution
        resolution.validation_results = validation_result.get("validation_results")
        resolution.confidence_score = validation_result.get("confidence_score")
        resolution.validation_status = validation_result.get("approval_status")
        resolution.model_agreement_metrics = validation_result.get("model_agreement")
        resolution.status = "validated" if validation_result.get("approval_status") == "approved" else "draft"
        resolution.updated_at = get_ist_time()
    
    db.commit()
    db.refresh(resolution)
    
    # Store individual model validations
    if validation_result.get("validation_results"):
        # Clear old validations
        db.query(ModelValidation).filter(
            ModelValidation.resolution_id == resolution.id
        ).delete()
        
        # Add new validations
        for model_result in validation_result["validation_results"]:
            for criterion, score in model_result["scores"].items():
                model_validation = ModelValidation(
                    resolution_id=resolution.id,
                    model_name=model_result["model"],
                    validation_type=criterion,
                    score=score,
                    feedback=model_result.get("feedback", ""),
                    passed=score >= 0.70
                )
                db.add(model_validation)
        
        db.commit()
    
    # Log action
    log_agent_action(
        db, agent.id, "submit_validation",
        complaint_id=complaint.id,
        ticket_id=ticket_id,
        details={
            "confidence_score": validation_result.get("confidence_score"),
            "approval_status": validation_result.get("approval_status")
        },
        request=request
    )
    
    return {
        "message": "Validation completed",
        "resolution_id": resolution.id,
        **validation_result
    }

# ============================================
# RESOLUTION ENDPOINTS
# ============================================

@router.post("/send-resolution")
def send_resolution(
    agent_email: str,
    ticket_id: str,
    final_solution: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Send verified resolution to user
    
    Request Body:
    {
        "agent_email": "agent@example.com",
        "ticket_id": "QF-2025-001",
        "final_solution": "Final verified solution..."
    }
    """
    # Verify agent access
    agent = require_agent_access(agent_email, db)
    
    # Get complaint
    complaint = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ticket ID {ticket_id} not found"
        )
    
    # Get resolution
    resolution = db.query(AgentResolution).filter(
        AgentResolution.complaint_id == complaint.id
    ).first()
    
    # Check if solution was validated
    if not resolution or resolution.validation_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solution must be validated and approved before sending"
        )
    
    # Update resolution
    resolution.final_solution = final_solution
    resolution.status = "sent"
    resolution.resolution_timestamp = get_ist_time()
    resolution.updated_at = get_ist_time()
    
    # Mark complaint as resolved
    complaint.is_resolved = True
    complaint.updated_at = get_ist_time()
    
    db.commit()
    
    # Send email to user
    try:
        email_service.send_agent_resolution(
            user_email=complaint.email,
            user_name=complaint.name,
            ticket_id=ticket_id,
            complaint_subject=complaint.subject or "Your Complaint",
            agent_solution=final_solution,
            agent_name=agent.full_name or agent.email
        )
        
        resolution.status = "delivered"
        db.commit()
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        # Don't fail the request, just log the error
    
    # Log action
    log_agent_action(
        db, agent.id, "send_resolution",
        complaint_id=complaint.id,
        ticket_id=ticket_id,
        details={"resolution_id": resolution.id},
        request=request
    )
    
    return {
        "message": "Resolution sent successfully",
        "ticket_id": ticket_id,
        "resolution_id": resolution.id,
        "status": resolution.status
    }

@router.get("/resolutions")
def get_all_resolutions(
    agent_email: str,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    min_confidence: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all agent resolutions with filters
    """
    # Verify agent access
    agent = require_agent_access(agent_email, db)
    
    # Build query
    query = db.query(AgentResolution, Complaint).join(
        Complaint, AgentResolution.complaint_id == Complaint.id
    )
    
    # Apply filters
    if category:
        query = query.filter(Complaint.category == category)
    
    if sentiment:
        query = query.filter(Complaint.sentiment == sentiment)
    
    if min_confidence:
        query = query.filter(AgentResolution.confidence_score >= min_confidence)
    
    if start_date:
        query = query.filter(AgentResolution.created_at >= start_date)
    
    if end_date:
        query = query.filter(AgentResolution.created_at <= end_date)
    
    # Order by most recent
    query = query.order_by(desc(AgentResolution.created_at))
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()
    
    # Format response
    resolutions = []
    for resolution, complaint in results:
        resolutions.append({
            "complaint_id": complaint.id,
            "ticket_id": resolution.ticket_id,
            "user_name": complaint.name,
            "user_email": complaint.email,
            "category": complaint.category,
            "sentiment": complaint.sentiment,
            "agent_name": resolution.agent_name,
            "final_solution": resolution.final_solution[:200] + "..." if len(resolution.final_solution) > 200 else resolution.final_solution,
            "confidence_score": resolution.confidence_score,
            "validation_status": resolution.validation_status,
            "resolution_timestamp": resolution.resolution_timestamp.isoformat() if resolution.resolution_timestamp else None,
            "status": resolution.status
        })
    
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit,
        "resolutions": resolutions
    }

@router.get("/audit-logs")
def get_audit_logs(
    agent_email: str,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get agent audit logs
    """
    # Verify agent access (admin only for viewing all logs)
    agent = require_agent_access(agent_email, db)
    
    # Build query
    query = db.query(AgentAuditLog)
    
    # Non-admins can only see their own logs
    if agent.role != "Admin":
        query = query.filter(AgentAuditLog.agent_id == agent.id)
    
    # Apply filters
    if action:
        query = query.filter(AgentAuditLog.action == action)
    
    if start_date:
        query = query.filter(AgentAuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AgentAuditLog.timestamp <= end_date)
    
    # Order by most recent
    query = query.order_by(desc(AgentAuditLog.timestamp))
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    logs = query.offset(offset).limit(limit).all()
    
    # Format response
    audit_logs = []
    for log in logs:
        audit_logs.append({
            "id": log.id,
            "agent_id": log.agent_id,
            "action": log.action,
            "ticket_id": log.ticket_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })
    
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit,
        "logs": audit_logs
    }
