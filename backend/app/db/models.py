"""
ORM models. The schema itself is owned by the versioned migrations in
app/db/migrations — tests assert that the migrated schema matches these models.
"""
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    text,
)

from app.db.database import Base, get_ist_time

ROLE_CUSTOMER = "customer"
ROLE_AGENT = "agent"
ROLE_ADMIN = "admin"
ROLES = (ROLE_CUSTOMER, ROLE_AGENT, ROLE_ADMIN)

CATEGORIES = ("Billing", "Technical", "Delivery", "Service", "Security", "Other")
PRIORITIES = ("High", "Medium", "Low")
SENTIMENTS = ("Positive", "Neutral", "Negative", "Angry")

STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_AWAITING_APPROVAL = "awaiting_approval"
STATUS_RESOLVED = "resolved"
STATUS_CLOSED = "closed"
COMPLAINT_STATUSES = (STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_AWAITING_APPROVAL, STATUS_RESOLVED, STATUS_CLOSED)

OTP_REGISTRATION = "registration"
OTP_VERIFY_EMAIL = "verify_email"
OTP_LOGIN = "login"
OTP_PASSWORD_RESET = "password_reset"
OTP_PURPOSES = (OTP_REGISTRATION, OTP_VERIFY_EMAIL, OTP_LOGIN, OTP_PASSWORD_RESET)


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    version = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    applied_at = Column(DateTime, nullable=False)


class User(Base):
    """An account. Only verified email addresses ever reach this table via signup."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20), nullable=True)
    legacy_phone = Column(String(40), nullable=True)
    organization = Column(String(100), nullable=True)
    profile_image = Column(Text, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    bio = Column(Text, nullable=True)
    job_title = Column(String(100))
    location = Column(String(100), default="India")
    created_at = Column(DateTime, default=get_ist_time)

    role = Column(String(20), nullable=False, default=ROLE_CUSTOMER)
    email_verified = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    department = Column(String(50), nullable=True)
    token_version = Column(Integer, nullable=False, default=0)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True, default=get_ist_time, onupdate=get_ist_time)

    __table_args__ = (
        CheckConstraint("role IN ('customer','agent','admin')", name="ck_users_role"),
        Index("uq_users_phone", "phone", unique=True, sqlite_where=text("phone IS NOT NULL")),
        Index("ix_users_role", "role"),
    )


class PendingRegistration(Base):
    """Signup data held until the email OTP is verified. Never an account."""

    __tablename__ = "pending_registrations"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False, unique=True)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    organization = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=get_ist_time)
    expires_at = Column(DateTime, nullable=False)


class EmailOTP(Base):
    """One issued code. Only an HMAC of the code is stored."""

    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    purpose = Column(String(30), nullable=False)
    code_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, nullable=False, default=get_ist_time)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    consumed_at = Column(DateTime, nullable=True)
    invalidated_at = Column(DateTime, nullable=True)
    ip_address = Column(String(64), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "purpose IN ('registration','verify_email','login','password_reset')", name="ck_email_otps_purpose"
        ),
        Index("ix_email_otps_email_purpose_created", "email", "purpose", "created_at"),
        Index("ix_email_otps_email_created", "email", "created_at"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True)
    family_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=get_ist_time)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by_id = Column(Integer, nullable=True)
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)


class RevokedAccessToken(Base):
    __tablename__ = "revoked_access_tokens"

    jti = Column(String(64), primary_key=True)
    expires_at = Column(DateTime, nullable=False, index=True)


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    login_method = Column(String(50), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(100), nullable=True)
    login_location = Column(String(255), nullable=True)
    success = Column(Boolean, default=True)
    status = Column(String(50), default="Completed")
    failure_reason = Column(String(255), nullable=True)
    login_time = Column(DateTime, default=get_ist_time, index=True)
    logout_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_ist_time)


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    subject = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    complaint_text = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)
    sentiment = Column(String(20))
    sentiment_score = Column(Float, default=0.0)
    response = Column(Text)
    solution = Column(Text)
    satisfaction_prediction = Column(String(20))
    action = Column(String(255))
    similar_complaints = Column(Text)
    ai_analysis_steps = Column(Text, nullable=True)
    user_rating = Column(Integer, nullable=True)
    user_feedback = Column(Text, nullable=True)
    user_resolution_feedback = Column(Boolean, nullable=True)
    user_resolution_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_ist_time, index=True)
    updated_at = Column(DateTime, default=get_ist_time, onupdate=get_ist_time)
    is_resolved = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), nullable=False, default=STATUS_OPEN, index=True)
    assigned_agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    requires_human_review = Column(Boolean, nullable=False, default=False)
    review_reason = Column(String(255), nullable=True)
    ai_provider = Column(String(50), nullable=True)
    ai_model = Column(String(120), nullable=True)
    ai_latency_ms = Column(Integer, nullable=True)
    ai_fallback_used = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('open','in_progress','awaiting_approval','resolved','closed')", name="ck_complaints_status"
        ),
    )


class ComplaintEvent(Base):
    """Append-only history of everything that happened to a complaint."""

    __tablename__ = "complaint_events"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role = Column(String(20), nullable=True)
    event_type = Column(String(50), nullable=False)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=get_ist_time, index=True)


class ComplaintAttachment(Base):
    __tablename__ = "complaint_attachments"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, nullable=False, default=get_ist_time)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    ticket_id = Column(String(50), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=get_ist_time)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_notifications_user_read", "user_id", "is_read", "created_at"),)


class AIExecutionLog(Base):
    __tablename__ = "ai_execution_logs"

    id = Column(Integer, primary_key=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True, index=True)
    operation = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=True)
    model = Column(String(120), nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    fallback_used = Column(Boolean, nullable=False, default=False)
    latency_ms = Column(Integer, nullable=True)
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=get_ist_time, index=True)


class AgentResolution(Base):
    __tablename__ = "agent_resolutions"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    ticket_id = Column(String(50), index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    draft_solution = Column(Text, nullable=True)
    final_solution = Column(Text, nullable=False)
    steps = Column(Text, nullable=True)
    validation_results = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    validation_status = Column(String(50), default="pending")
    model_agreement_metrics = Column(JSON, nullable=True)
    resolution_timestamp = Column(DateTime, nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=get_ist_time, index=True)
    updated_at = Column(DateTime, default=get_ist_time, onupdate=get_ist_time)

    requires_approval = Column(Boolean, nullable=False, default=False)
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)


class ModelValidation(Base):
    __tablename__ = "model_validations"

    id = Column(Integer, primary_key=True, index=True)
    resolution_id = Column(Integer, ForeignKey("agent_resolutions.id"), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    validation_type = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    passed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_ist_time)


class AgentAuditLog(Base):
    """Audit trail for staff (agent and admin) actions. `agent_id` is the actor."""

    __tablename__ = "agent_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    complaint_id = Column(Integer, nullable=True)
    ticket_id = Column(String(50), nullable=True, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=get_ist_time, index=True)
