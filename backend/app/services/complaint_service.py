"""
Complaint workflow and access control.

Access policy (enforced here, used by every complaint endpoint):
  * customer — only complaints they own (complaints.user_id).
  * agent    — complaints assigned to them; unassigned ones too only when
               AGENT_CAN_VIEW_UNASSIGNED=true.
  * admin    — everything.
Anything outside a user's scope is reported as 404, so ticket ids cannot be
probed for existence.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import string
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, bad_request, forbidden, not_found
from app.db.database import get_ist_time
from app.db.models import (
    ROLE_ADMIN,
    ROLE_AGENT,
    ROLE_CUSTOMER,
    STATUS_AWAITING_APPROVAL,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    STATUS_RESOLVED,
    AgentResolution,
    AIExecutionLog,
    Complaint,
    ComplaintAttachment,
    ComplaintEvent,
    ModelValidation,
    User,
)
from app.schemas.complaint import complaint_to_dict
from app.services.activity import notify, notify_admins, record_event

ACTIVE_STATUSES = (STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_AWAITING_APPROVAL)

# Which status changes staff may make by hand. Resolution happens through the
# send-resolution flow so the customer always receives the solution.
STAFF_TRANSITIONS = {
    STATUS_OPEN: {STATUS_IN_PROGRESS, STATUS_CLOSED},
    STATUS_IN_PROGRESS: {STATUS_OPEN, STATUS_RESOLVED, STATUS_CLOSED},
    STATUS_AWAITING_APPROVAL: {STATUS_IN_PROGRESS},
    STATUS_RESOLVED: {STATUS_IN_PROGRESS, STATUS_CLOSED},
    STATUS_CLOSED: {STATUS_IN_PROGRESS},
}

ALLOWED_UPLOADS = {
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "application/pdf": (b"%PDF-",),
    "text/plain": (),
}


# ---------------------------------------------------------------------------
# Scoping
# ---------------------------------------------------------------------------

def scope_query(query, user: User):
    if user.role == ROLE_ADMIN:
        return query
    if user.role == ROLE_AGENT:
        if get_settings().agent_can_view_unassigned:
            return query.where(or_(Complaint.assigned_agent_id == user.id, Complaint.assigned_agent_id.is_(None)))
        return query.where(Complaint.assigned_agent_id == user.id)
    return query.where(Complaint.user_id == user.id)


def get_for_user(db: Session, user: User, ticket_id: str) -> Complaint:
    complaint = db.execute(
        scope_query(select(Complaint).where(Complaint.ticket_id == ticket_id), user)
    ).scalar_one_or_none()
    if complaint is None:
        raise not_found("Complaint not found", "COMPLAINT_NOT_FOUND")
    return complaint


def is_staff(user: User) -> bool:
    return user.role in (ROLE_AGENT, ROLE_ADMIN)


def serialize(db: Session, user: User, complaints: List[Complaint]) -> List[dict]:
    agent_ids = {c.assigned_agent_id for c in complaints if c.assigned_agent_id}
    names = {}
    if agent_ids:
        names = dict(db.execute(select(User.id, User.full_name).where(User.id.in_(agent_ids))).all())
    counts = {}
    ids = [c.id for c in complaints]
    if ids:
        counts = dict(db.execute(
            select(ComplaintAttachment.complaint_id, func.count(ComplaintAttachment.id))
            .where(ComplaintAttachment.complaint_id.in_(ids)).group_by(ComplaintAttachment.complaint_id)
        ).all())
    staff = is_staff(user)
    return [complaint_to_dict(c, staff, names.get(c.assigned_agent_id), counts.get(c.id, 0)) for c in complaints]


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------

def new_ticket_id() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return f"QX-{get_ist_time():%Y%m%d}-{''.join(secrets.choice(alphabet) for _ in range(6))}"


def pick_agent(db: Session, category: str) -> Optional[User]:
    """Department routing: agents of the matching department first, then least-loaded agent overall."""
    load = (
        select(Complaint.assigned_agent_id.label("agent_id"), func.count(Complaint.id).label("n"))
        .where(Complaint.status.in_(ACTIVE_STATUSES), Complaint.assigned_agent_id.is_not(None))
        .group_by(Complaint.assigned_agent_id).subquery()
    )
    base = (
        select(User).outerjoin(load, load.c.agent_id == User.id)
        .where(User.role == ROLE_AGENT, User.is_active.is_(True), User.email_verified.is_(True))
        .order_by(func.coalesce(load.c.n, 0), User.id)
    )
    return (db.execute(base.where(User.department == category).limit(1)).scalar_one_or_none()
            or db.execute(base.limit(1)).scalar_one_or_none())


def create_complaint(db: Session, user: User, subject: str, description: str, ai: Dict) -> Tuple[Complaint, dict]:
    now = get_ist_time()
    agent = pick_agent(db, ai["category"])
    for _attempt in range(5):
        complaint = Complaint(
            ticket_id=new_ticket_id(), user_id=user.id, name=user.full_name or user.email.split("@")[0],
            email=user.email, subject=subject, description=description, complaint_text=description,
            category=ai["category"], priority=ai["priority"], sentiment=ai["sentiment"],
            response=ai.get("response", ""), solution=ai.get("solution", ""), action=ai.get("action", ""),
            satisfaction_prediction=ai.get("satisfaction"), similar_complaints=ai.get("similar_issues", ""),
            ai_analysis_steps=json.dumps(ai.get("steps", [])), status=STATUS_OPEN, is_resolved=False,
            requires_human_review=bool(ai.get("requires_human_review")), review_reason=ai.get("review_reason"),
            ai_provider=ai.get("ai_provider"), ai_model=ai.get("ai_model"), ai_latency_ms=ai.get("ai_latency_ms"),
            ai_fallback_used=bool(ai.get("fallback_used")), created_at=now, updated_at=now,
            assigned_agent_id=agent.id if agent else None, assigned_at=now if agent else None,
        )
        db.add(complaint)
        try:
            db.flush()
            break
        except IntegrityError:
            db.rollback()  # ticket id collision — astronomically rare, but retry
    else:
        raise AppError(500, "Could not allocate a ticket number. Please try again.", "TICKET_ALLOCATION_FAILED")

    record_event(db, complaint, "created", user, to_status=STATUS_OPEN)
    record_event(db, complaint, "ai_analysis", None, note=(
        f"{ai['category']} / {ai['priority']} / {ai['sentiment']}"
        + (" (offline analysis)" if ai.get("fallback_used") else "")), actor_role="system")
    db.add(AIExecutionLog(
        complaint_id=complaint.id, operation="complaint_analysis", provider=ai.get("ai_provider"),
        model=ai.get("ai_model"), success=not ai.get("fallback_used"), fallback_used=bool(ai.get("fallback_used")),
        latency_ms=ai.get("ai_latency_ms"), error=(ai.get("ai_error") or None) and ai["ai_error"][:500],
        created_at=now,
    ))
    if ai.get("injection_flags"):
        record_event(db, complaint, "security_flag", None, actor_role="system",
                     note="Possible prompt injection: " + ", ".join(ai["injection_flags"]))
    if agent:
        record_event(db, complaint, "assigned", None, actor_role="system", note=f"Auto-assigned to {agent.full_name}")
        notify(db, agent.id, "assignment", f"New complaint {complaint.ticket_id}",
               f"{complaint.category} / {complaint.priority}: {subject}", complaint.ticket_id)
    notify(db, user.id, "complaint_created", f"Complaint {complaint.ticket_id} received",
           "We have received your complaint and will keep you updated here.", complaint.ticket_id)
    if complaint.requires_human_review or not agent:
        notify_admins(db, "review_needed", f"Complaint {complaint.ticket_id} needs attention",
                      complaint.review_reason or "No agent available for assignment", complaint.ticket_id)
    db.commit()
    return complaint, serialize(db, user, [complaint])[0]


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------

def list_for_user(db: Session, user: User, *, status: Optional[str] = None, priority: Optional[str] = None,
                  category: Optional[str] = None, sentiment: Optional[str] = None, search: Optional[str] = None,
                  assigned: Optional[str] = None, needs_review: Optional[bool] = None,
                  sort: str = "newest", page: int = 1, page_size: int = 20) -> dict:
    query = scope_query(select(Complaint), user)
    if status:
        query = query.where(Complaint.status == status)
    if priority:
        query = query.where(Complaint.priority == priority)
    if category:
        query = query.where(Complaint.category == category)
    if sentiment:
        query = query.where(Complaint.sentiment == sentiment)
    if needs_review is not None and is_staff(user):
        query = query.where(Complaint.requires_human_review.is_(needs_review))
    if assigned and user.role == ROLE_ADMIN:
        if assigned == "unassigned":
            query = query.where(Complaint.assigned_agent_id.is_(None))
        elif assigned.isdigit():
            query = query.where(Complaint.assigned_agent_id == int(assigned))
    if search:
        term = f"%{search.strip()[:100]}%"
        fields = [Complaint.ticket_id.like(term), Complaint.subject.like(term), Complaint.description.like(term)]
        if is_staff(user):
            fields += [Complaint.name.like(term), Complaint.email.like(term)]
        query = query.where(or_(*fields))

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    priority_rank = case((Complaint.priority == "High", 0), (Complaint.priority == "Medium", 1), else_=2)
    order = {
        "oldest": [Complaint.created_at.asc()],
        "priority": [priority_rank, Complaint.created_at.desc()],
        "updated": [Complaint.updated_at.desc()],
    }.get(sort, [Complaint.created_at.desc()])
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    rows = db.execute(query.order_by(*order, Complaint.id.desc())
                      .offset((page - 1) * page_size).limit(page_size)).scalars().all()
    items = serialize(db, user, rows)
    return {"items": items, "complaints": items, "total": total, "page": page, "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size}


def history(db: Session, user: User, complaint: Complaint) -> List[dict]:
    query = select(ComplaintEvent, User.full_name).outerjoin(User, User.id == ComplaintEvent.actor_id) \
        .where(ComplaintEvent.complaint_id == complaint.id).order_by(ComplaintEvent.created_at, ComplaintEvent.id)
    events = []
    for event, actor_name in db.execute(query).all():
        if not is_staff(user) and event.event_type in ("internal_note", "security_flag", "ai_analysis"):
            continue
        events.append({
            "id": event.id, "type": event.event_type, "from_status": event.from_status,
            "to_status": event.to_status, "note": event.note, "created_at": event.created_at,
            "actor": (actor_name if is_staff(user) or event.actor_role == ROLE_CUSTOMER else "Support team")
            if event.actor_id else ("System" if event.actor_role == "system" else None),
            "actor_role": event.actor_role,
        })
    return events


# ---------------------------------------------------------------------------
# Status, assignment, deletion
# ---------------------------------------------------------------------------

def set_status(db: Session, actor: User, complaint: Complaint, new_status: str, note: Optional[str] = None) -> None:
    old = complaint.status or STATUS_OPEN
    if new_status == old:
        return
    if new_status not in STAFF_TRANSITIONS.get(old, set()):
        raise bad_request(f"Cannot change status from {old} to {new_status}.", "INVALID_TRANSITION")
    if new_status == STATUS_RESOLVED and not (complaint.solution or "").strip():
        raise bad_request("Add a solution before marking the complaint resolved.", "SOLUTION_REQUIRED")
    if new_status == STATUS_RESOLVED and complaint.requires_human_review and actor.role not in (ROLE_AGENT, ROLE_ADMIN):
        raise forbidden()
    now = get_ist_time()
    complaint.status = new_status
    complaint.is_resolved = new_status in (STATUS_RESOLVED, STATUS_CLOSED)
    complaint.resolved_at = now if complaint.is_resolved else None
    complaint.updated_at = now
    record_event(db, complaint, "status_changed", actor, from_status=old, to_status=new_status, note=note)
    labels = {STATUS_IN_PROGRESS: "is being worked on", STATUS_RESOLVED: "has been resolved",
              STATUS_CLOSED: "has been closed", STATUS_OPEN: "was reopened", STATUS_AWAITING_APPROVAL: "is under review"}
    notify(db, complaint.user_id, "status_changed", f"Complaint {complaint.ticket_id} {labels.get(new_status, new_status)}",
           note or f"Status changed to {new_status.replace('_', ' ')}.", complaint.ticket_id)


def assign(db: Session, admin: User, complaint: Complaint, agent_id: Optional[int]) -> None:
    agent = None
    if agent_id is not None:
        agent = db.get(User, agent_id)
        if agent is None or agent.role != ROLE_AGENT or not agent.is_active:
            raise bad_request("Choose an active support agent.", "INVALID_AGENT")
    complaint.assigned_agent_id = agent.id if agent else None
    complaint.assigned_at = get_ist_time() if agent else None
    complaint.updated_at = get_ist_time()
    record_event(db, complaint, "assigned", admin,
                 note=f"Assigned to {agent.full_name}" if agent else "Unassigned")
    if agent:
        notify(db, agent.id, "assignment", f"Complaint {complaint.ticket_id} assigned to you",
               complaint.subject or "", complaint.ticket_id)


def delete_complaints(db: Session, complaint_ids: List[int]) -> int:
    if not complaint_ids:
        return 0
    resolution_ids = [r for (r,) in db.execute(
        select(AgentResolution.id).where(AgentResolution.complaint_id.in_(complaint_ids)))]
    if resolution_ids:
        db.query(ModelValidation).filter(ModelValidation.resolution_id.in_(resolution_ids)).delete(
            synchronize_session=False)
        db.query(AgentResolution).filter(AgentResolution.id.in_(resolution_ids)).delete(synchronize_session=False)
    for model in (ComplaintEvent, ComplaintAttachment):
        db.query(model).filter(model.complaint_id.in_(complaint_ids)).delete(synchronize_session=False)
    db.query(AIExecutionLog).filter(AIExecutionLog.complaint_id.in_(complaint_ids)).update(
        {AIExecutionLog.complaint_id: None}, synchronize_session=False)
    count = db.query(Complaint).filter(Complaint.id.in_(complaint_ids)).delete(synchronize_session=False)
    db.commit()
    return count


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

def _sniff(content_type: str, data: bytes) -> bool:
    signatures = ALLOWED_UPLOADS.get(content_type)
    if signatures is None:
        return False
    if content_type == "text/plain":
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return b"\x00" not in data
    return any(data.startswith(sig) for sig in signatures)


def safe_filename(name: str) -> str:
    base = (name or "attachment").replace("\\", "/").split("/")[-1]
    cleaned = "".join(ch for ch in base if ch.isalnum() or ch in "._- ").strip(" .")
    return (cleaned or "attachment")[:120]


def add_attachment(db: Session, user: User, complaint: Complaint, filename: str, content_type: str,
                   data: bytes) -> ComplaintAttachment:
    s = get_settings()
    if not data:
        raise bad_request("The file is empty.", "EMPTY_FILE")
    if len(data) > s.max_upload_bytes:
        raise AppError(413, f"Files must be {s.max_upload_bytes // 1_000_000} MB or smaller.", "FILE_TOO_LARGE")
    content_type = (content_type or "").split(";")[0].strip().lower()
    if not _sniff(content_type, data):
        raise AppError(415, "Only PNG, JPEG, PDF or plain-text files are accepted.", "UNSUPPORTED_FILE_TYPE")
    existing = db.execute(select(func.count(ComplaintAttachment.id))
                          .where(ComplaintAttachment.complaint_id == complaint.id)).scalar_one()
    if existing >= s.max_attachments_per_complaint:
        raise bad_request(f"A complaint can have at most {s.max_attachments_per_complaint} attachments.",
                          "TOO_MANY_ATTACHMENTS")
    attachment = ComplaintAttachment(
        complaint_id=complaint.id, uploaded_by=user.id, filename=safe_filename(filename), content_type=content_type,
        size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), data=data, created_at=get_ist_time(),
    )
    db.add(attachment)
    record_event(db, complaint, "attachment_added", user, note=attachment.filename)
    db.commit()
    return attachment


def list_attachments(db: Session, complaint: Complaint) -> List[dict]:
    rows = db.execute(
        select(ComplaintAttachment.id, ComplaintAttachment.filename, ComplaintAttachment.content_type,
               ComplaintAttachment.size_bytes, ComplaintAttachment.created_at)
        .where(ComplaintAttachment.complaint_id == complaint.id).order_by(ComplaintAttachment.id)
    ).all()
    return [dict(id=r.id, filename=r.filename, content_type=r.content_type, size_bytes=r.size_bytes,
                 created_at=r.created_at) for r in rows]


def stats(db: Session, user: Optional[User] = None) -> dict:
    base = select(Complaint)
    if user is not None:
        base = scope_query(base, user)
    sub = base.subquery()
    by = lambda col: dict(db.execute(select(col, func.count()).select_from(sub).group_by(col)).all())  # noqa: E731
    total = db.execute(select(func.count()).select_from(sub)).scalar_one()
    since = get_ist_time() - timedelta(days=13)
    daily = db.execute(
        select(func.substr(sub.c.created_at, 1, 10), func.count()).select_from(sub)
        .where(sub.c.created_at >= since).group_by(func.substr(sub.c.created_at, 1, 10))
    ).all()
    resolved_durations = db.execute(
        select(func.avg((func.julianday(sub.c.resolved_at) - func.julianday(sub.c.created_at)) * 24.0))
        .select_from(sub).where(and_(sub.c.resolved_at.is_not(None), sub.c.created_at.is_not(None)))
    ).scalar_one()
    return {
        "total": total,
        "by_status": by(sub.c.status),
        "by_category": by(sub.c.category),
        "by_priority": by(sub.c.priority),
        "by_sentiment": by(sub.c.sentiment),
        "needs_review": db.execute(select(func.count()).select_from(sub).where(
            sub.c.requires_human_review.is_(True), sub.c.status.in_(ACTIVE_STATUSES))).scalar_one(),
        "avg_resolution_hours": round(resolved_durations, 1) if resolved_durations is not None else None,
        "daily": [{"date": d, "count": n} for d, n in sorted(daily)],
    }
