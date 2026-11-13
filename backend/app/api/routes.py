"""Complaint API. Every route requires authentication and applies the access policy in complaint_service."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_agent_pipeline
from app.api.deps import get_current_user, require_admin, require_customer, require_staff
from app.core.errors import bad_request, forbidden, not_found
from app.core.rate_limit import rate_limit
from app.db.database import get_db, get_ist_time
from app.db.models import (
    ROLE_ADMIN,
    ROLE_CUSTOMER,
    STATUS_IN_PROGRESS,
    STATUS_RESOLVED,
    Complaint,
    ComplaintAttachment,
    User,
)
from app.schemas.complaint import (
    AssignRequest,
    BulkDeleteRequest,
    ComplaintRequest,
    ResolutionFeedbackRequest,
    ReviewRequest,
    StatusUpdateRequest,
)
from app.services import complaint_service as svc
from app.services.activity import audit, notify, notify_admins, record_event
from app.services.auto_resolver import auto_resolver
from app.services.email_service import email_service

router = APIRouter(tags=["complaints"])


@router.post("/complaint", status_code=201, dependencies=[Depends(rate_limit("complaint:create", 10, 600))])
async def submit_complaint(data: ComplaintRequest, background_tasks: BackgroundTasks,
                           user: User = Depends(require_customer), db: Session = Depends(get_db)):
    """File a complaint as the signed-in customer. AI triage runs before the ticket is stored."""
    ai = await run_agent_pipeline(f"Subject: {data.subject}\nDescription: {data.description}")
    complaint, payload = await run_in_threadpool(svc.create_complaint, db, user, data.subject, data.description, ai)
    background_tasks.add_task(auto_resolver.process_complaint, complaint.id)
    email_service.send_complaint_confirmation(user.full_name or "Customer", user.email, {
        "ticket_id": complaint.ticket_id, "subject": complaint.subject, "description": complaint.description,
        "category": complaint.category, "priority": complaint.priority, "sentiment": complaint.sentiment,
        "response": complaint.response, "solution": "" if complaint.requires_human_review else complaint.solution,
        "action": complaint.action,
    })
    if complaint.requires_human_review:
        # Not reviewed by a human yet: the customer sees the acknowledgement, not the AI's draft fix.
        payload["solution"] = ""
    payload.update({"satisfaction": complaint.satisfaction_prediction, "similar_issues": complaint.similar_complaints,
                    "churn_risk": ai.get("churn_risk"), "urgency_data": ai.get("urgency_data", {}),
                    "requires_human_review": complaint.requires_human_review})
    return payload


@router.get("/complaints")
def list_complaints(
    status: Optional[str] = None, priority: Optional[str] = None, category: Optional[str] = None,
    sentiment: Optional[str] = None, search: Optional[str] = Query(None, max_length=100),
    assigned: Optional[str] = None, needs_review: Optional[bool] = None, sort: str = "newest",
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Customers get their own complaints, agents their assigned ones, admins everything."""
    return svc.list_for_user(db, user, status=status, priority=priority, category=category, sentiment=sentiment,
                             search=search, assigned=assigned, needs_review=needs_review, sort=sort,
                             page=page, page_size=page_size)


@router.get("/complaints/stats")
def complaint_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.stats(db, user)


@router.get("/complaints/{ticket_id}")
def get_complaint(ticket_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    complaint = svc.get_for_user(db, user, ticket_id)
    data = svc.serialize(db, user, [complaint])[0]
    if user.role == ROLE_CUSTOMER and complaint.requires_human_review and complaint.status != STATUS_RESOLVED:
        data["solution"] = ""
    return data


@router.get("/complaints/{ticket_id}/history")
def complaint_history(ticket_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"events": svc.history(db, user, svc.get_for_user(db, user, ticket_id))}


@router.post("/complaint/{ticket_id}/review")
def review_complaint(ticket_id: str, data: ReviewRequest, user: User = Depends(require_customer),
                     db: Session = Depends(get_db)):
    complaint = svc.get_for_user(db, user, ticket_id)
    complaint.user_rating = data.rating
    complaint.user_feedback = data.feedback
    record_event(db, complaint, "customer_review", user, note=f"Rated {data.rating}/5")
    db.commit()
    return {"message": "Review submitted successfully", "ticket_id": ticket_id}


@router.post("/complaint/{ticket_id}/resolution-feedback")
def resolution_feedback(ticket_id: str, data: ResolutionFeedbackRequest, user: User = Depends(require_customer),
                        db: Session = Depends(get_db)):
    """Customer confirms the fix worked, or reopens the complaint."""
    complaint = svc.get_for_user(db, user, ticket_id)
    complaint.user_resolution_feedback = data.is_actually_resolved
    complaint.user_resolution_comment = data.user_comment
    old = complaint.status
    now = get_ist_time()
    if data.is_actually_resolved:
        complaint.status, complaint.is_resolved = STATUS_RESOLVED, True
        complaint.resolved_at = complaint.resolved_at or now
    else:
        complaint.status, complaint.is_resolved, complaint.resolved_at = STATUS_IN_PROGRESS, False, None
    complaint.updated_at = now
    record_event(db, complaint, "customer_feedback", user, from_status=old, to_status=complaint.status,
                 note=data.user_comment or ("Confirmed resolved" if data.is_actually_resolved else "Not resolved"))
    if not data.is_actually_resolved:
        notify(db, complaint.assigned_agent_id, "reopened", f"Complaint {ticket_id} reopened by customer",
               data.user_comment or "The customer reports the issue is not resolved.", ticket_id)
        notify_admins(db, "reopened", f"Complaint {ticket_id} reopened", data.user_comment or "", ticket_id)
    db.commit()
    email_service.send_resolution_feedback_to_admin(
        user_name=complaint.name, user_email=complaint.email, ticket_id=ticket_id, subject=complaint.subject,
        is_actually_resolved=data.is_actually_resolved, user_comment=data.user_comment or "",
        original_solution=complaint.solution or "No solution provided")
    return {"message": "Feedback submitted successfully", "ticket_id": ticket_id,
            "is_actually_resolved": data.is_actually_resolved, "status": complaint.status}


@router.patch("/complaint/{ticket_id}/status")
def update_status(ticket_id: str, data: StatusUpdateRequest, request: Request,
                  user: User = Depends(require_staff), db: Session = Depends(get_db)):
    """Staff status change. Assigned agents and admins only."""
    complaint = svc.get_for_user(db, user, ticket_id)
    target = data.status or (STATUS_RESOLVED if data.is_resolved else STATUS_IN_PROGRESS if data.is_resolved is False
                             else None)
    if target is None:
        raise bad_request("Provide a status.", "STATUS_REQUIRED")
    if data.admin_solution:
        complaint.solution = data.admin_solution
    old = complaint.status
    svc.set_status(db, user, complaint, target, data.note)
    audit(db, user, "update_status", request, complaint, {"from": old, "to": target})
    db.commit()
    if target == STATUS_RESOLVED and old != STATUS_RESOLVED:
        email_service.send_resolution_email(name=complaint.name, email=complaint.email, ticket_id=ticket_id,
                                            subject=complaint.subject, solution=complaint.solution or "")
    return {"message": "Status updated", "ticket_id": ticket_id, "status": complaint.status,
            "is_resolved": complaint.is_resolved}


@router.patch("/complaints/{ticket_id}/assign")
def assign_complaint(ticket_id: str, data: AssignRequest, request: Request, admin: User = Depends(require_admin),
                     db: Session = Depends(get_db)):
    complaint = svc.get_for_user(db, admin, ticket_id)
    svc.assign(db, admin, complaint, data.agent_id)
    audit(db, admin, "assign_complaint", request, complaint, {"agent_id": data.agent_id})
    db.commit()
    return {"message": "Assignment updated", "ticket_id": ticket_id, "assigned_agent_id": complaint.assigned_agent_id}


@router.delete("/complaint/{ticket_id}")
def delete_complaint(ticket_id: str, request: Request, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """Customers may delete their own complaints; admins any. Agents cannot delete."""
    if user.role not in (ROLE_CUSTOMER, ROLE_ADMIN):
        raise forbidden()
    complaint = svc.get_for_user(db, user, ticket_id)
    if user.role == ROLE_ADMIN:
        audit(db, user, "delete_complaint", request, complaint)
        db.commit()
    svc.delete_complaints(db, [complaint.id])
    return {"message": "Complaint deleted successfully", "ticket_id": ticket_id}


@router.delete("/complaints")
def delete_my_complaints(user: User = Depends(require_customer), db: Session = Depends(get_db)):
    """Delete all of the signed-in customer's complaints."""
    ids = [cid for (cid,) in db.execute(select(Complaint.id).where(Complaint.user_id == user.id))]
    count = svc.delete_complaints(db, ids)
    return {"message": f"Deleted {count} complaints", "deleted_count": count}


@router.delete("/complaints/bulk")
@router.post("/complaints/bulk-delete")
def bulk_delete(payload: BulkDeleteRequest, request: Request, admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    ids = [cid for (cid,) in db.execute(select(Complaint.id).where(Complaint.id.in_(payload.ids)))]
    audit(db, admin, "bulk_delete_complaints", request, None, {"ids": ids})
    db.commit()
    count = svc.delete_complaints(db, ids)
    return {"message": f"Deleted {count} complaints", "deleted_count": count}


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

@router.post("/complaints/{ticket_id}/attachments", status_code=201,
             dependencies=[Depends(rate_limit("complaint:upload", 20, 600))])
async def upload_attachment(ticket_id: str, file: UploadFile = File(...), user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    from app.core.config import get_settings

    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)
    complaint = await run_in_threadpool(svc.get_for_user, db, user, ticket_id)
    if user.role != ROLE_CUSTOMER and user.role != ROLE_ADMIN and complaint.assigned_agent_id != user.id:
        raise forbidden()
    attachment = await run_in_threadpool(svc.add_attachment, db, user, complaint, file.filename or "",
                                         file.content_type or "", data)
    return {"id": attachment.id, "filename": attachment.filename, "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes}


@router.get("/complaints/{ticket_id}/attachments")
def list_attachments(ticket_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"attachments": svc.list_attachments(db, svc.get_for_user(db, user, ticket_id))}


@router.get("/complaints/{ticket_id}/attachments/{attachment_id}")
def download_attachment(ticket_id: str, attachment_id: int, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    complaint = svc.get_for_user(db, user, ticket_id)
    attachment = db.execute(select(ComplaintAttachment).where(
        ComplaintAttachment.id == attachment_id, ComplaintAttachment.complaint_id == complaint.id)).scalar_one_or_none()
    if attachment is None:
        raise not_found("Attachment not found")
    return Response(content=attachment.data, media_type=attachment.content_type, headers={
        "Content-Disposition": f'attachment; filename="{attachment.filename}"',
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'; sandbox",
    })
