"""Admin API. Every route requires the admin role."""
import csv
import io
from datetime import timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import get_settings
from app.core.errors import bad_request, not_found
from app.db.database import describe_target, get_db, get_ist_time, resolve_turso_target
from app.db.models import (
    CATEGORIES,
    ROLE_ADMIN,
    ROLE_AGENT,
    AIExecutionLog,
    Complaint,
    LoginHistory,
    User,
)
from app.services import complaint_service as svc
from app.services.activity import audit, notify
from app.services.auth_service import revoke_all_sessions, user_payload

router = APIRouter(prefix="/admin", tags=["admin"])


class UserAdminUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Optional[Literal["customer", "agent", "admin"]] = None
    is_active: Optional[bool] = None
    department: Optional[Literal["Billing", "Technical", "Delivery", "Service", "Security", "Other", ""]] = None


@router.get("/overview")
def overview(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users_by_role = dict(db.execute(select(User.role, func.count(User.id)).group_by(User.role)).all())
    since = get_ist_time() - timedelta(days=30)
    ai = db.execute(select(func.count(AIExecutionLog.id),
                           func.sum(case((AIExecutionLog.fallback_used.is_(True), 1), else_=0)),
                           func.avg(AIExecutionLog.latency_ms))
                    .where(AIExecutionLog.operation == "complaint_analysis", AIExecutionLog.created_at >= since)).one()
    return {
        "complaints": svc.stats(db),
        "users": {"by_role": users_by_role, "total": sum(users_by_role.values()),
                  "unverified": db.execute(select(func.count(User.id)).where(User.email_verified.is_(False))).scalar_one()},
        "ai_last_30_days": {"analyses": ai[0] or 0, "fallbacks": int(ai[1] or 0),
                            "avg_latency_ms": int(ai[2]) if ai[2] is not None else None},
    }


@router.get("/users")
def list_users(search: Optional[str] = Query(None, max_length=100), role: Optional[str] = None,
               page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if search:
        term = f"%{search.strip().lower()}%"
        query = query.where(or_(User.email.like(term), func.lower(User.full_name).like(term), User.phone.like(term)))
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    rows = db.execute(query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)).scalars().all()
    open_counts = dict(db.execute(
        select(Complaint.assigned_agent_id, func.count(Complaint.id))
        .where(Complaint.status.in_(svc.ACTIVE_STATUSES), Complaint.assigned_agent_id.is_not(None))
        .group_by(Complaint.assigned_agent_id)).all())
    items = []
    for u in rows:
        data = user_payload(u)
        data.pop("profile_image", None)
        data["open_assigned"] = open_counts.get(u.id, 0)
        items.append(data)
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size}


@router.patch("/users/{user_id}")
def update_user(user_id: int, data: UserAdminUpdate, request: Request, admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    """Change a user's role, department or active state. Admins cannot demote or disable themselves."""
    target = db.get(User, user_id)
    if target is None:
        raise not_found("User not found")
    changes = data.model_dump(exclude_unset=True)
    if target.id == admin.id and (changes.get("role", ROLE_ADMIN) != ROLE_ADMIN or changes.get("is_active") is False):
        raise bad_request("You cannot remove your own admin access or disable your own account.", "SELF_LOCKOUT")
    if "role" in changes and changes["role"] != target.role:
        if not target.email_verified:
            raise bad_request("Only verified accounts can be given staff roles.", "UNVERIFIED_ACCOUNT")
        old_role = target.role
        target.role = changes["role"]
        revoke_all_sessions(db, target)  # force new tokens carrying the new role
        if old_role == ROLE_AGENT:
            db.query(Complaint).filter(Complaint.assigned_agent_id == target.id,
                                       Complaint.status.in_(svc.ACTIVE_STATUSES)).update(
                {Complaint.assigned_agent_id: None, Complaint.assigned_at: None}, synchronize_session=False)
        notify(db, target.id, "role_changed", "Your access was updated", f"Your role is now {target.role}.")
    if "is_active" in changes and changes["is_active"] != target.is_active:
        target.is_active = changes["is_active"]
        if not target.is_active:
            revoke_all_sessions(db, target)
    if "department" in changes:
        target.department = changes["department"] or None
    audit(db, admin, "update_user", request, None, {"user_id": target.id, **{k: v for k, v in changes.items()}})
    db.commit()
    return user_payload(target)


@router.get("/agents")
def list_agents(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    agents = db.execute(select(User).where(User.role == ROLE_AGENT).order_by(User.full_name)).scalars().all()
    load = dict(db.execute(select(Complaint.assigned_agent_id, func.count(Complaint.id))
                           .where(Complaint.status.in_(svc.ACTIVE_STATUSES)).group_by(Complaint.assigned_agent_id)).all())
    resolved = dict(db.execute(select(Complaint.assigned_agent_id, func.count(Complaint.id))
                               .where(Complaint.status.in_(("resolved", "closed"))).group_by(Complaint.assigned_agent_id)).all())
    return {"items": [{"id": a.id, "full_name": a.full_name, "email": a.email, "department": a.department,
                       "is_active": a.is_active, "open_assigned": load.get(a.id, 0),
                       "resolved": resolved.get(a.id, 0), "last_login_at": a.last_login_at} for a in agents]}


@router.get("/categories")
def categories(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """The AI taxonomy is fixed in code; this reports volumes and which agents cover each department."""
    counts = dict(db.execute(select(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category)).all())
    open_counts = dict(db.execute(select(Complaint.category, func.count(Complaint.id))
                                  .where(Complaint.status.in_(svc.ACTIVE_STATUSES)).group_by(Complaint.category)).all())
    agents = dict(db.execute(select(User.department, func.count(User.id))
                             .where(User.role == ROLE_AGENT, User.is_active.is_(True)).group_by(User.department)).all())
    return {"items": [{"name": c, "total": counts.get(c, 0), "open": open_counts.get(c, 0),
                       "agents": agents.get(c, 0)} for c in CATEGORIES]}


@router.get("/ai/logs")
def ai_logs(operation: Optional[str] = None, fallback_only: bool = False, page: int = Query(1, ge=1),
            page_size: int = Query(50, ge=1, le=200), admin: User = Depends(require_admin),
            db: Session = Depends(get_db)):
    query = select(AIExecutionLog, Complaint.ticket_id).outerjoin(Complaint, Complaint.id == AIExecutionLog.complaint_id)
    if operation:
        query = query.where(AIExecutionLog.operation == operation)
    if fallback_only:
        query = query.where(AIExecutionLog.fallback_used.is_(True))
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    rows = db.execute(query.order_by(desc(AIExecutionLog.created_at)).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"id": log.id, "ticket_id": ticket, "operation": log.operation, "provider": log.provider,
                       "model": log.model, "success": log.success, "fallback_used": log.fallback_used,
                       "latency_ms": log.latency_ms, "error": log.error, "created_at": log.created_at}
                      for log, ticket in rows],
            "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


@router.get("/ai/summary")
def ai_summary(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(select(AIExecutionLog.operation, AIExecutionLog.provider, AIExecutionLog.model,
                             func.count(AIExecutionLog.id), func.avg(AIExecutionLog.latency_ms))
                      .group_by(AIExecutionLog.operation, AIExecutionLog.provider, AIExecutionLog.model)).all()
    review = db.execute(select(func.count(Complaint.id)).where(Complaint.requires_human_review.is_(True))).scalar_one()
    total = db.execute(select(func.count(Complaint.id))).scalar_one()
    return {"by_model": [{"operation": op, "provider": p, "model": m, "calls": n,
                          "avg_latency_ms": int(avg) if avg is not None else None} for op, p, m, n, avg in rows],
            "complaints_requiring_review": review, "complaints_total": total}


@router.get("/audit-logs")
def admin_audit_logs(action: Optional[str] = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200),
                     admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    from app.routes.agent_module import audit_logs

    return audit_logs(action=action, page=page, limit=limit, user=admin, db=db)


@router.get("/login-history")
def login_history(email: Optional[str] = None, limit: int = Query(100, ge=1, le=500),
                  admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = select(LoginHistory)
    if email:
        query = query.where(LoginHistory.email == email.strip().lower())
    rows = db.execute(query.order_by(desc(LoginHistory.login_time)).limit(limit)).scalars().all()
    return {"total": len(rows), "records": [{
        "id": r.id, "user_id": r.user_id, "user_name": r.user_name or r.email.split("@")[0], "email": r.email,
        "phone": r.phone, "login_method": r.login_method, "ip_address": r.ip_address, "user_agent": r.user_agent,
        "device_type": r.device_type, "login_location": r.login_location, "success": r.success, "status": r.status,
        "failure_reason": r.failure_reason, "login_time": r.login_time, "logout_time": r.logout_time,
        "created_at": r.created_at} for r in rows]}


@router.get("/login-stats")
def login_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    total = db.execute(select(func.count(LoginHistory.id))).scalar_one()
    ok = db.execute(select(func.count(LoginHistory.id)).where(LoginHistory.success.is_(True))).scalar_one()
    methods = dict(db.execute(select(LoginHistory.login_method, func.count(LoginHistory.id))
                              .group_by(LoginHistory.login_method)).all())
    failures = db.execute(select(LoginHistory).where(LoginHistory.success.is_(False))
                          .order_by(desc(LoginHistory.login_time)).limit(10)).scalars().all()
    return {"total_logins": total, "successful_logins": ok, "failed_logins": total - ok,
            "success_rate": round(ok / total * 100, 2) if total else 0, "methods": methods,
            "recent_failures": [{"email": r.email, "method": r.login_method, "reason": r.failure_reason,
                                 "time": r.login_time} for r in failures]}


@router.delete("/login-history/{history_id}")
def delete_login_history(history_id: int, request: Request, admin: User = Depends(require_admin),
                         db: Session = Depends(get_db)):
    record = db.get(LoginHistory, history_id)
    if record is None:
        raise not_found("Record not found")
    db.delete(record)
    audit(db, admin, "delete_login_history", request, None, {"history_id": history_id})
    db.commit()
    return {"message": "Record deleted successfully"}


@router.get("/reports/complaints.csv")
def export_complaints(status: Optional[str] = None, category: Optional[str] = None,
                      admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = select(Complaint)
    if status:
        query = query.where(Complaint.status == status)
    if category:
        query = query.where(Complaint.category == category)
    rows = db.execute(query.order_by(Complaint.created_at.desc()).limit(10_000)).scalars().all()
    agents = dict(db.execute(select(User.id, User.full_name).where(User.role == ROLE_AGENT)).all())
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ticket_id", "created_at", "status", "category", "priority", "sentiment", "customer",
                     "customer_email", "subject", "assigned_agent", "requires_review", "ai_provider", "ai_model",
                     "resolved_at", "rating"])

    def cell(value):
        text = "" if value is None else str(value)
        return "'" + text if text[:1] in ("=", "+", "-", "@") else text  # CSV formula-injection guard

    for c in rows:
        writer.writerow([cell(v) for v in (c.ticket_id, c.created_at, c.status, c.category, c.priority, c.sentiment,
                                           c.name, c.email, c.subject, agents.get(c.assigned_agent_id),
                                           c.requires_human_review, c.ai_provider, c.ai_model, c.resolved_at,
                                           c.user_rating)])
    buffer.seek(0)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": 'attachment; filename="complaints.csv"'})


@router.get("/system")
def system_status(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Read-only configuration status (no secret values)."""
    from app.db.database import engine
    from app.db.migrations import applied_versions, pending_migrations

    s = get_settings()
    database, _ = resolve_turso_target(s.turso_database_url, s.turso_auth_token)
    return {
        "environment": s.environment,
        "database": {"engine": "Turso (libSQL)", "target": describe_target(database),
                     "migrations_applied": applied_versions(engine),
                     "migrations_pending": [m.version for m in pending_migrations(engine)]},
        "email": {"transport": s.email_transport, "configured": s.email_configured,
                  "from": s.smtp_from_email or None, "admin_notifications": bool(s.admin_notification_email)},
        "ai": {"groq_configured": bool(s.groq_api_key), "gemini_configured": bool(s.gemini_api_key),
               "timeout_seconds": s.ai_timeout_seconds, "auto_resolve_delay_seconds": s.auto_resolve_delay_seconds,
               "auto_resolve_min_confidence": s.auto_resolve_min_confidence},
        "auth": {"access_token_minutes": s.access_token_minutes, "refresh_token_days": s.refresh_token_days,
                 "otp_ttl_seconds": s.otp_ttl_seconds, "otp_resend_cooldown_seconds": s.otp_resend_cooldown_seconds,
                 "otp_max_per_hour": s.otp_max_per_hour, "google_sign_in": bool(s.google_client_id)},
        "policy": {"agent_can_view_unassigned": s.agent_can_view_unassigned,
                   "max_upload_bytes": s.max_upload_bytes},
    }
