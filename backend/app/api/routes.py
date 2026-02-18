from fastapi import APIRouter, HTTPException, Depends, Body, BackgroundTasks
from sqlalchemy.orm import Session
from app.agents.orchestrator import run_agent_pipeline
from app.db.database import get_db, get_ist_time
from app.db.models import Complaint
from app.schemas.complaint import ComplaintRequest, ComplaintResponse, BulkDeleteRequest
from app.services.email_service import email_service
from app.services.auto_resolver import auto_resolver
import datetime
import random
import string
import json

router = APIRouter()

@router.post("/complaint", response_model=ComplaintResponse)
async def handle_complaint(
    data: ComplaintRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Handle complaint submission and run AI analysis pipeline (Async version for scaling)
    """
    try:
        print(f"📋 New Complaint: {data.subject}")

        # Combine subject and description for comprehensive AI analysis
        full_text = f"Subject: {data.subject}\nDescription: {data.description}"
        
        # Run AI agents pipeline asynchronously
        result = await run_agent_pipeline(full_text)
        
        category = result.get("category", "Other")
        priority = result.get("priority", "Low")
        response = result.get("response", "")
        action = result.get("action", "")
        sentiment = result.get("sentiment", "Neutral")
        solution = result.get("solution", "")
        satisfaction = result.get("satisfaction", "Medium")
        similar = result.get("similar_issues", "")
        steps = result.get("steps", [])

        # Generate Professional Ticket ID
        date_str = get_ist_time().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        ticket_id = f"QX-{date_str}-{random_str}"

        # Save to database
        complaint = Complaint(
            ticket_id=ticket_id,
            name=data.name,
            email=data.email,
            subject=data.subject,
            description=data.description,
            complaint_text=data.description, # Mirror to legacy field for DB compatibility
            category=category,
            priority=priority,
            response=response,
            action=action,
            sentiment=sentiment,
            solution=solution,
            satisfaction_prediction=satisfaction,
            similar_complaints=similar,
            ai_analysis_steps=json.dumps(steps), # Save orchestrated steps
            is_resolved=False
        )

        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        # Trigger auto-resolution pipeline in the background
        # This will validate the solution and mail it if confidence is high
        background_tasks.add_task(auto_resolver.process_complaint, complaint.id)

        # Send confirmation email
        email_service.send_complaint_confirmation(data.name, data.email, {
            "ticket_id": ticket_id,
            "subject": data.subject,
            "description": data.description,
            "category": category,
            "priority": priority,
            "sentiment": sentiment,
            "response": response,
            "solution": solution,
            "action": action,
        })

        return ComplaintResponse(
            ticket_id=ticket_id,
            subject=data.subject,
            description=data.description,
            category=category,
            priority=priority,
            response=response,
            action=action,
            sentiment=sentiment,
            solution=solution,
            satisfaction=satisfaction,
            similar_issues=similar,
            steps=steps
        )

    except Exception as e:
        print("❌ BACKEND EXCEPTION:", repr(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complaint/{ticket_id}/review")
async def review_complaint(ticket_id: str, rating: int = Body(..., embed=True), feedback: str = Body(None, embed=True), db: Session = Depends(get_db)):
    """
    Allow users to review the AI solution
    """
    try:
        complaint = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        complaint.user_rating = rating
        complaint.user_feedback = feedback
        db.commit()
        
        return {"message": "Review submitted successfully", "ticket_id": ticket_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/complaints")
def get_all_complaints(email: str = None, db: Session = Depends(get_db)):
    try:
        if not email: return {"total": 0, "complaints": []}
        from app.db.models import User
        user = db.query(User).filter(User.email == email).first()
        if user and user.role == "Admin":
            complaints = db.query(Complaint).all()
        else:
            complaints = db.query(Complaint).filter(Complaint.email == email).all()
        return {"total": len(complaints), "complaints": complaints}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/complaints")
def delete_complaints(email: str = None, db: Session = Depends(get_db)):
    try:
        if not email: raise HTTPException(status_code=400, detail="Email required")
        count = db.query(Complaint).filter(Complaint.email == email).delete(synchronize_session=False)
        db.commit()
        return {"message": f"Deleted {count} complaints", "deleted_count": count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
@router.patch("/complaint/{ticket_id}/status")
async def update_complaint_status(
    ticket_id: str, 
    is_resolved: bool = Body(..., embed=True), 
    admin_solution: str = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """
    Update complaint resolution status and send resolution email with solution
    """
    try:
        complaint = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        complaint.is_resolved = is_resolved
        complaint.updated_at = get_ist_time()
        
        # If admin provides a solution, update it
        if admin_solution:
            complaint.solution = admin_solution
        
        db.commit()
        
        # Send resolution email to user when marked as resolved
        if is_resolved:
            email_service.send_resolution_email(
                name=complaint.name,
                email=complaint.email,
                ticket_id=ticket_id,
                subject=complaint.subject,
                solution=admin_solution or complaint.solution or "Your issue has been resolved by our team."
            )
        
        return {
            "message": "Status updated successfully", 
            "ticket_id": ticket_id, 
            "is_resolved": is_resolved,
            "email_sent": is_resolved
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/complaint/{ticket_id}")
async def delete_complaint(ticket_id: str, db: Session = Depends(get_db)):
    """
    Delete a single complaint by ticket_id
    """
    try:
        complaint = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        # Delete associated records manually to satisfy foreign key constraints
        from app.db.models import AgentResolution, ModelValidation
        
        # 1. Get complaint ID
        complaint_id = complaint.id
        
        # 2. Find associated resolutions
        resolutions = db.query(AgentResolution).filter(AgentResolution.complaint_id == complaint_id).all()
        resolution_ids = [r.id for r in resolutions]
        
        if resolution_ids:
            # 3. Delete model validations for these resolutions
            db.query(ModelValidation).filter(ModelValidation.resolution_id.in_(resolution_ids)).delete(synchronize_session=False)
            
            # 4. Delete resolutions
            db.query(AgentResolution).filter(AgentResolution.id.in_(resolution_ids)).delete(synchronize_session=False)

        db.delete(complaint)
        db.commit()
        
        return {
            "message": "Complaint deleted successfully",
            "ticket_id": ticket_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/complaints/bulk")
async def bulk_delete_complaints(payload: BulkDeleteRequest, db: Session = Depends(get_db)):
    """
    Delete multiple complaints by ids and handle associated records
    """
    try:
        complaint_ids = payload.ids
        if not complaint_ids:
            return {"message": "No IDs provided", "deleted_count": 0}

        from app.db.models import AgentResolution, ModelValidation
        
        # 1. Find associated resolutions
        resolutions = db.query(AgentResolution).filter(AgentResolution.complaint_id.in_(complaint_ids)).all()
        resolution_ids = [r.id for r in resolutions]
        
        if resolution_ids:
            # 2. Delete associated model validations
            db.query(ModelValidation).filter(ModelValidation.resolution_id.in_(resolution_ids)).delete(synchronize_session=False)
            
            # 3. Delete associated resolutions
            db.query(AgentResolution).filter(AgentResolution.id.in_(resolution_ids)).delete(synchronize_session=False)

        # 4. Delete complaints
        count = db.query(Complaint).filter(Complaint.id.in_(complaint_ids)).delete(synchronize_session=False)
        db.commit()
        
        return {"message": f"Successfully deleted {count} complaints and associated data", "deleted_count": count}
    except Exception as e:
        db.rollback()
        print(f"❌ BULK DELETE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complaint/{ticket_id}/resolution-feedback")
async def submit_resolution_feedback(
    ticket_id: str,
    is_actually_resolved: bool = Body(..., embed=True),
    user_comment: str = Body("", embed=True),
    db: Session = Depends(get_db)
):
    """
    Allow users to provide feedback on whether their complaint was actually resolved.
    Sends notification to admin if user reports it's not resolved.
    """
    try:
        complaint = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Store the feedback
        complaint.user_resolution_feedback = is_actually_resolved
        complaint.user_resolution_comment = user_comment
        
        # If user says it is resolved, mark the ticket as resolved
        if is_actually_resolved:
            complaint.is_resolved = True
        else:
            # If user says it is NOT resolved, ensure it is marked as open
            complaint.is_resolved = False
            
        complaint.updated_at = get_ist_time()
        db.commit()
        
        # Send email to admin with user's feedback
        email_service.send_resolution_feedback_to_admin(
            user_name=complaint.name,
            user_email=complaint.email,
            ticket_id=ticket_id,
            subject=complaint.subject,
            is_actually_resolved=is_actually_resolved,
            user_comment=user_comment,
            original_solution=complaint.solution or "No solution provided"
        )
        
        return {
            "message": "Feedback submitted successfully",
            "ticket_id": ticket_id,
            "is_actually_resolved": is_actually_resolved
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

