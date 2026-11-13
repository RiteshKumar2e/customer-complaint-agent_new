"""
Support-agent workspace: queue, complaint review, AI validation and sending
human-approved resolutions. Identity comes from the access token (the old
`agent_email` parameter is ignored). Agents only reach complaints assigned to
them; admins reach all.
"""
import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_staff
from app.core.config import get_settings
from app.core.errors import bad_request, forbidden
from app.db.database import get_db, get_ist_time
from app.db.models import (
    ROLE_ADMIN,
    STATUS_AWAITING_APPROVAL,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    STATUS_RESOLVED,
    AgentAuditLog,
    AgentResolution,
    AIExecutionLog,
    Complaint,
    ModelValidation,
    User,
)
from app.schemas.complaint import NoteRequest, ResolutionRequest
from app.services import complaint_service as svc
from app.services.activity import audit, notify, record_event
from app.services.email_service import email_service
from app.services.multi_model_validator import multi_model_validator

router = APIRouter(prefix="/agent", tags=["agent-workspace"])


def normalize_steps(steps: Optional[List[Any]]) -> Optional[List[str]]:
    """Coerce steps (strings or the pipeline's {"step","status"} dicts) to short plain strings."""
    if not steps:
        return None
    normalized = []
    for step in steps[:20]:
        if step is None:
            continue
        if isinstance(step, dict):
            label = step.get("step") or step.get("title") or step.get("name") or ""
            detail = step.get("status") or step.get("description") or step.get("detail") or ""
            text = " — ".join(p for p in (str(label).strip(), str(detail).strip()) if p) or json.dumps(step)
        else:
            text = str(step).strip()
        if text:
            normalized.append(text[:500])
    return normalized or None


def _resolution_dict(resolution: Optional[AgentResolution]) -> Optional[dict]:
    if resolution is None:
        return None
    return {
        "id": resolution.id, "draft_solution": resolution.draft_solution, "final_solution": resolution.final_solution,
        "steps": json.loads(resolution.steps) if resolution.steps else None,
        "validation_status": resolution.validation_status, "confidence_score": resolution.confidence_score,
        "status": resolution.status, "requires_approval": bool(resolution.requires_approval),
        "agent_name": resolution.agent_name, "created_at": resolution.created_at,
    }


@router.get("/complaints/queue")
def complaint_queue(
    status: Optional[str] = None, priority: Optional[str] = None, sentiment: Optional[str] = None,
    category: Optional[str] = None, search: Optional[str] = Query(None, max_length=100),
    sort_by: str = "created_at", sort_order: str = "desc", needs_review: Optional[bool] = None,
    page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_staff), db: Session = Depends(get_db),
):
    legacy = {"pending": None, "resolved": STATUS_RESOLVED}
    status_filter = legacy.get(status, status) if status in legacy else status
    sort = "priority" if sort_by == "priority" else ("oldest" if sort_order == "asc" else "newest")
    result = svc.list_for_user(db, user, status=status_filter, priority=priority, category=category,
                               sentiment=sentiment, search=search, needs_review=needs_review, sort=sort,
                               page=page, page_size=limit)
    if status == "pending":  # legacy filter meaning "not resolved"
        result["items"] = [c for c in result["items"] if c["status"] in svc.ACTIVE_STATUSES]
        result["complaints"] = result["items"]
    ids = [c["id"] for c in result["items"]]
    resolutions = {}
    if ids:
        for r in db.execute(select(AgentResolution).where(AgentResolution.complaint_id.in_(ids))).scalars():
            resolutions[r.complaint_id] = r
    for item in result["items"]:
        res = resolutions.get(item["id"])
        item["agent_status"] = res.status if res else None
        item["agent_name"] = res.agent_name if res else None
        item["user_name"], item["user_email"] = item["name"], item["email"]
    result["limit"] = result["page_size"]
    return result


@router.get("/complaints/{ticket_id}")
def complaint_detail(ticket_id: str, request: Request, user: User = Depends(require_staff),
                     db: Session = Depends(get_db)):
    complaint = svc.get_for_user(db, user, ticket_id)
    audit(db, user, "view_complaint", request, complaint)
    db.commit()
    resolution = db.execute(select(AgentResolution).where(AgentResolution.complaint_id == complaint.id)).scalar_one_or_none()
    data = svc.serialize(db, user, [complaint])[0]
    data.update({"user_name": complaint.name, "user_email": complaint.email, "ai_response": complaint.response,
                 "ai_solution": complaint.solution, "ai_steps": data["steps"], "ai_action": complaint.action})
    return {"complaint": data, "agent_resolution": _resolution_dict(resolution),
            "history": svc.history(db, user, complaint), "attachments": svc.list_attachments(db, complaint)}


@router.post("/complaints/{ticket_id}/claim")
def claim(ticket_id: str, request: Request, user: User = Depends(require_staff), db: Session = Depends(get_db)):
    """Take ownership of an unassigned complaint (only when AGENT_CAN_VIEW_UNASSIGNED is enabled)."""
    complaint = svc.get_for_user(db, user, ticket_id)
    if complaint.assigned_agent_id not in (None, user.id):
        raise bad_request("This complaint is already assigned to another agent.", "ALREADY_ASSIGNED")
    if user.role != ROLE_ADMIN and not get_settings().agent_can_view_unassigned and complaint.assigned_agent_id is None:
        raise forbidden()
    complaint.assigned_agent_id, complaint.assigned_at = user.id, get_ist_time()
    record_event(db, complaint, "assigned", user, note=f"Claimed by {user.full_name}")
    if complaint.status == STATUS_OPEN:
        svc.set_status(db, user, complaint, STATUS_IN_PROGRESS)
    audit(db, user, "claim_complaint", request, complaint)
    db.commit()
    return {"message": "Complaint assigned to you", "ticket_id": ticket_id}


@router.post("/complaints/{ticket_id}/notes")
def add_note(ticket_id: str, data: NoteRequest, request: Request, user: User = Depends(require_staff),
             db: Session = Depends(get_db)):
    """Internal note (staff only) or a public reply that the customer sees in their timeline."""
    complaint = svc.get_for_user(db, user, ticket_id)
    record_event(db, complaint, "internal_note" if data.internal else "agent_reply", user, note=data.note)
    if not data.internal:
        notify(db, complaint.user_id, "agent_reply", f"New reply on {ticket_id}", data.note[:300], ticket_id)
        if complaint.status == STATUS_OPEN:
            svc.set_status(db, user, complaint, STATUS_IN_PROGRESS)
    complaint.updated_at = get_ist_time()
    audit(db, user, "add_note", request, complaint, {"internal": data.internal})
    db.commit()
    return {"message": "Note added"}


@router.post("/validate-solution")
async def validate_solution(data: ResolutionRequest, request: Request, user: User = Depends(require_staff),
                            db: Session = Depends(get_db)):
    """Score a draft with the multi-model validator. Advisory only: a human decides what is sent."""
    from fastapi.concurrency import run_in_threadpool

    draft = data.text()
    steps = normalize_steps(data.steps)
    complaint = await run_in_threadpool(svc.get_for_user, db, user, data.ticket_id)
    started = get_ist_time()
    result = await multi_model_validator.validate_solution({
        "category": complaint.category, "priority": complaint.priority, "sentiment": complaint.sentiment,
        "subject": complaint.subject, "description": complaint.description or complaint.complaint_text,
    }, draft)

    def persist():
        resolution = db.execute(select(AgentResolution).where(AgentResolution.complaint_id == complaint.id)).scalar_one_or_none()
        if resolution is None:
            resolution = AgentResolution(complaint_id=complaint.id, ticket_id=complaint.ticket_id, agent_id=user.id,
                                         agent_name=user.full_name or user.email, final_solution=draft)
            db.add(resolution)
        resolution.draft_solution = draft
        if steps:
            resolution.steps = json.dumps(steps)
        resolution.validation_results = result.get("validation_results")
        resolution.confidence_score = result.get("confidence_score")
        resolution.validation_status = result.get("approval_status")
        resolution.model_agreement_metrics = result.get("model_agreement")
        if resolution.status not in ("sent", "delivered"):
            resolution.status = "validated" if result.get("approval_status") == "approved" else "draft"
        resolution.updated_at = get_ist_time()
        db.flush()
        db.query(ModelValidation).filter(ModelValidation.resolution_id == resolution.id).delete()
        for model_result in result.get("validation_results") or []:
            for criterion, score in (model_result.get("scores") or {}).items():
                db.add(ModelValidation(resolution_id=resolution.id, model_name=model_result["model"],
                                       validation_type=criterion, score=score, feedback=model_result.get("feedback", ""),
                                       passed=score >= 0.70))
        db.add(AIExecutionLog(complaint_id=complaint.id, operation="solution_validation", provider="groq",
                              model=",".join(r["model"] for r in result.get("validation_results") or [])[:120] or None,
                              success=bool(result.get("validation_results")), fallback_used=False,
                              latency_ms=int((get_ist_time() - started).total_seconds() * 1000),
                              error=result.get("error")))
        audit(db, user, "submit_validation", request, complaint,
              {"confidence_score": result.get("confidence_score"), "approval_status": result.get("approval_status")})
        db.commit()
        return resolution.id

    resolution_id = await run_in_threadpool(persist)
    return {"message": "Validation completed", "resolution_id": resolution_id, **result}


@router.post("/send-resolution")
def send_resolution(data: ResolutionRequest, request: Request, user: User = Depends(require_staff),
                    db: Session = Depends(get_db)):
    """Send a human-approved resolution to the customer and resolve the complaint."""
    final = data.text()
    steps = normalize_steps(data.steps)
    complaint = svc.get_for_user(db, user, data.ticket_id)
    if complaint.status in (STATUS_RESOLVED,) and complaint.user_resolution_feedback is True:
        raise bad_request("The customer has already confirmed this complaint is resolved.", "ALREADY_RESOLVED")
    now = get_ist_time()
    resolution = db.execute(select(AgentResolution).where(AgentResolution.complaint_id == complaint.id)).scalar_one_or_none()
    if resolution is None:
        resolution = AgentResolution(complaint_id=complaint.id, ticket_id=complaint.ticket_id, agent_id=user.id,
                                     agent_name=user.full_name or user.email, draft_solution=final,
                                     final_solution=final, validation_status="skipped")
        db.add(resolution)
    resolution.final_solution = final
    resolution.agent_id, resolution.agent_name = user.id, user.full_name or user.email
    if steps:
        resolution.steps = json.dumps(steps)
    resolution.status = "sent"
    resolution.resolution_timestamp = now
    resolution.approved_by_id, resolution.approved_at = user.id, now
    resolution.updated_at = now

    old = complaint.status
    complaint.solution = final
    if steps:
        complaint.ai_analysis_steps = json.dumps([{"step": s, "status": "action"} for s in steps])
    complaint.status, complaint.is_resolved, complaint.resolved_at, complaint.updated_at = STATUS_RESOLVED, True, now, now
    if complaint.assigned_agent_id is None and user.role != ROLE_ADMIN:
        complaint.assigned_agent_id, complaint.assigned_at = user.id, now
    db.flush()
    record_event(db, complaint, "resolution_sent", user, from_status=old, to_status=STATUS_RESOLVED,
                 note=final[:2000])
    notify(db, complaint.user_id, "resolution", f"Resolution for {complaint.ticket_id}",
           "A support agent has sent a resolution for your complaint. Please let us know if it worked.",
           complaint.ticket_id)
    audit(db, user, "send_resolution", request, complaint,
          {"resolution_id": resolution.id, "was_awaiting_approval": old == STATUS_AWAITING_APPROVAL})
    db.commit()
    email_service.send_agent_resolution(user_email=complaint.email, user_name=complaint.name,
                                        ticket_id=complaint.ticket_id,
                                        complaint_subject=complaint.subject or "Your complaint",
                                        agent_solution=final, agent_name=user.full_name or "Support team",
                                        agent_steps=steps)
    resolution.status = "delivered"
    db.commit()
    return {"message": "Resolution sent successfully", "ticket_id": complaint.ticket_id,
            "resolution_id": resolution.id, "status": resolution.status}


@router.get("/resolutions")
def list_resolutions(category: Optional[str] = None, sentiment: Optional[str] = None,
                     search: Optional[str] = Query(None, max_length=100), min_confidence: Optional[float] = None,
                     page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                     user: User = Depends(require_staff), db: Session = Depends(get_db)):
    query = select(AgentResolution, Complaint).join(Complaint, AgentResolution.complaint_id == Complaint.id)
    if user.role != ROLE_ADMIN:
        query = query.where(or_(AgentResolution.agent_id == user.id, Complaint.assigned_agent_id == user.id))
    if category:
        query = query.where(Complaint.category == category)
    if sentiment:
        query = query.where(Complaint.sentiment == sentiment)
    if min_confidence is not None:
        query = query.where(AgentResolution.confidence_score >= min_confidence)
    if search:
        term = f"%{search}%"
        query = query.where(or_(AgentResolution.ticket_id.like(term), AgentResolution.agent_name.like(term),
                                Complaint.name.like(term), Complaint.subject.like(term)))
    from sqlalchemy import func

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    rows = db.execute(query.order_by(desc(AgentResolution.created_at)).offset((page - 1) * limit).limit(limit)).all()
    items = [{
        "id": r.id, "complaint_id": c.id, "ticket_id": r.ticket_id, "user_name": c.name, "user_email": c.email,
        "category": c.category, "sentiment": c.sentiment, "agent_name": r.agent_name,
        "final_solution": r.final_solution if len(r.final_solution or "") <= 200 else r.final_solution[:200] + "...",
        "confidence_score": r.confidence_score, "validation_status": r.validation_status, "status": r.status,
        "requires_approval": bool(r.requires_approval),
        "sent_at": r.resolution_timestamp, "resolution_timestamp": r.resolution_timestamp,
        "steps": json.loads(r.steps) if r.steps else [],
    } for r, c in rows]
    return {"items": items, "resolutions": items, "total": total, "page": page, "limit": limit,
            "total_pages": (total + limit - 1) // limit}


@router.get("/audit-logs")
def audit_logs(action: Optional[str] = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200),
               user: User = Depends(require_staff), db: Session = Depends(get_db)):
    """Agents see their own activity (work history); admins see everyone's."""
    from sqlalchemy import func

    query = select(AgentAuditLog, User.full_name).outerjoin(User, User.id == AgentAuditLog.agent_id)
    if user.role != ROLE_ADMIN:
        query = query.where(AgentAuditLog.agent_id == user.id)
    if action:
        query = query.where(AgentAuditLog.action == action)
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    rows = db.execute(query.order_by(desc(AgentAuditLog.timestamp)).offset((page - 1) * limit).limit(limit)).all()
    items = [{"id": log.id, "agent_id": log.agent_id, "actor_name": name, "action": log.action,
              "ticket_id": log.ticket_id, "details": log.details, "ip_address": log.ip_address,
              "timestamp": log.timestamp} for log, name in rows]
    return {"items": items, "logs": items, "total": total, "page": page, "limit": limit,
            "total_pages": (total + limit - 1) // limit}
