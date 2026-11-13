"""In-app notifications for the signed-in user."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import not_found
from app.db.database import get_db, get_ist_time
from app.db.models import Notification, User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(unread_only: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                       user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    unread = db.execute(select(func.count(Notification.id)).where(Notification.user_id == user.id,
                                                                  Notification.is_read.is_(False))).scalar_one()
    rows = db.execute(query.order_by(desc(Notification.created_at), desc(Notification.id))
                      .offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return {"items": [{"id": n.id, "type": n.type, "title": n.title, "message": n.message, "ticket_id": n.ticket_id,
                       "is_read": n.is_read, "created_at": n.created_at} for n in rows],
            "total": total, "unread": unread, "page": page, "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.execute(select(Notification).where(Notification.id == notification_id,
                                                 Notification.user_id == user.id)).scalar_one_or_none()
    if note is None:
        raise not_found("Notification not found")
    note.is_read, note.read_at = True, get_ist_time()
    db.commit()
    return {"message": "Marked as read"}


@router.post("/read-all")
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(update(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))
               .values(is_read=True, read_at=get_ist_time()))
    db.commit()
    return {"message": "All notifications marked as read"}
