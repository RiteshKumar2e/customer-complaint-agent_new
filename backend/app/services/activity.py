"""In-app notifications, complaint history events and the staff audit log."""
from __future__ import annotations

from typing import Iterable, Optional

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_ist_time
from app.db.models import ROLE_ADMIN, AgentAuditLog, Complaint, ComplaintEvent, Notification, User


def notify(db: Session, user_id: Optional[int], type_: str, title: str, message: str,
           ticket_id: Optional[str] = None) -> None:
    if not user_id:
        return
    db.add(Notification(user_id=user_id, type=type_, title=title[:200], message=message[:2000],
                        ticket_id=ticket_id, created_at=get_ist_time()))


def notify_admins(db: Session, type_: str, title: str, message: str, ticket_id: Optional[str] = None,
                  exclude: Iterable[int] = ()) -> None:
    skip = set(exclude)
    for (admin_id,) in db.execute(select(User.id).where(User.role == ROLE_ADMIN, User.is_active.is_(True))):
        if admin_id not in skip:
            notify(db, admin_id, type_, title, message, ticket_id)


def record_event(db: Session, complaint: Complaint, event_type: str, actor: Optional[User] = None,
                 from_status: Optional[str] = None, to_status: Optional[str] = None,
                 note: Optional[str] = None, actor_role: Optional[str] = None) -> None:
    db.add(ComplaintEvent(
        complaint_id=complaint.id,
        actor_id=actor.id if actor else None,
        actor_role=actor_role or (actor.role if actor else "system"),
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        note=(note or None) and note[:2000],
        created_at=get_ist_time(),
    ))


def audit(db: Session, actor: User, action: str, request: Optional[Request] = None,
          complaint: Optional[Complaint] = None, details: Optional[dict] = None) -> None:
    db.add(AgentAuditLog(
        agent_id=actor.id,
        action=action,
        complaint_id=complaint.id if complaint else None,
        ticket_id=complaint.ticket_id if complaint else None,
        details=details,
        ip_address=request.client.host if request is not None and request.client else None,
        user_agent=((request.headers.get("user-agent") if request is not None else "") or "")[:500] or None,
        timestamp=get_ist_time(),
    ))
