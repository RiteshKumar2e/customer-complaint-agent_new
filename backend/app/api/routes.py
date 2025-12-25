from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.agents.orchestrator import run_agent_pipeline
from app.db.database import get_db, get_ist_time
from app.db.models import Complaint
from app.schemas.complaint import ComplaintRequest, ComplaintResponse
from app.services.email_service import email_service
import datetime
import random
import string

router = APIRouter()


@router.post("/complaint", response_model=ComplaintResponse)
def handle_complaint(data: ComplaintRequest, db: Session = Depends(get_db)):
    """
    Handle complaint submission and run AI analysis pipeline
    """
    try:
        print("📋 Complaint received:", data.complaint)

        # Run AI agents pipeline
        result = run_agent_pipeline(data.complaint)
        print("🤖 Agent output:", result)

        if not isinstance(result, dict) or not all(key in result for key in ["category", "priority", "response", "action"]):
            raise ValueError("Invalid agent pipeline output")

        category = result.get("category", "Other")
        priority = result.get("priority", "Low")
        response = result.get("response", "")
        action = result.get("action", "")
        sentiment = result.get("sentiment", "Neutral")
        solution = result.get("solution", "")
        satisfaction = result.get("satisfaction", "Medium")
        similar = result.get("similar_issues", "")

        # Generate Professional Ticket ID (e.g. QX-20231027-A1B2)
        date_str = get_ist_time().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        ticket_id = f"QX-{date_str}-{random_str}"

        # Save to database with all fields including name and email
        complaint = Complaint(
            ticket_id=ticket_id,
            name=data.name,
            email=data.email,
            complaint_text=data.complaint,
            category=category,
            priority=priority,
            response=response,
            action=action,
            sentiment=sentiment,
            solution=solution,
            satisfaction_prediction=satisfaction,
            similar_complaints=similar,
            is_resolved=False
        )

        print(f"💾 Saving complaint {ticket_id} to database...")
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        print("✅ Complaint saved successfully!")

        # Prepare complaint data for email
        complaint_data = {
            "ticket_id": ticket_id,
            "complaint_text": data.complaint,
            "category": category,
            "priority": priority,
            "sentiment": sentiment,
            "response": response,
            "solution": solution,
            "action": action,
        }

        # Send confirmation email to user
        print("📧 Sending confirmation email...")
        email_service.send_complaint_confirmation(data.name, data.email, complaint_data)

        return ComplaintResponse(
            ticket_id=ticket_id,
            category=category,
            priority=priority,
            response=response,
            action=action,
            sentiment=sentiment,
            solution=solution,
            satisfaction=satisfaction,
            similar_issues=similar
        )

    except Exception as e:
        print("❌ BACKEND EXCEPTION:", repr(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complaints")
def get_all_complaints(email: str = None, db: Session = Depends(get_db)):
    """Get complaints. Normal users see only their own. Admins see all."""
    try:
        if not email:
            return {"total": 0, "complaints": []}
            
        # Check if user is admin
        from app.db.models import User
        user = db.query(User).filter(User.email == email).first()
        
        if user and user.role == "Admin":
            complaints = db.query(Complaint).all()
        else:
            complaints = db.query(Complaint).filter(Complaint.email == email).all()
        
        return {
            "total": len(complaints),
            "complaints": complaints
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complaints/{complaint_id}")
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    """Get specific complaint by ID"""
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        return complaint
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/complaints")
def delete_complaints(email: str = None, db: Session = Depends(get_db)):
    """Delete complaints for a specific user. Email is required for safety."""
    try:
        if not email:
            raise HTTPException(status_code=400, detail="Email is required to delete complaints")
            
        count = db.query(Complaint).filter(Complaint.email == email).delete(synchronize_session=False)
        db.commit()
        print(f"🗑️ Deleted {count} complaints from database for email: {email}")
        return {
            "message": f"Successfully deleted {count} complaints",
            "deleted_count": count
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
