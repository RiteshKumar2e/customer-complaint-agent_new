"""
0002 — authentication, RBAC and complaint-workflow schema.

Data handling for existing rows (no row is deleted):

users
  * `role` held a free-text job title that users could edit themselves (and
    set to "Admin"). It is renamed to `job_title`; a new `role` column holds
    the authorization role (customer/agent/admin). Everyone becomes
    `customer`, `is_agent=1` rows become `agent`. NOBODY is granted admin by
    this migration — admins must be provisioned with `python -m app.cli
    promote --email ... --role admin` (trusted server-side process).
  * emails are trimmed and lower-cased (aborts if that would create a clash).
  * phone numbers are normalised to 10 digits when they are valid Indian
    mobiles; anything else is moved to `legacy_phone` (kept, not used for auth).
  * `email_verified` starts false for every existing account: users confirm
    their address with an OTP on next login. Nothing is auto-verified.
  * plaintext `otp` / `otp_expiry` values (old OTPs and reset tokens) and the
    superseded `is_agent` flag are dropped.

complaints
  * new workflow/ownership/AI-metadata columns; `user_id` is back-filled by
    matching the complaint email to an account; `status` mirrors `is_resolved`.
"""
from sqlalchemy import text

from app.core.logging import get_logger
from app.core.validators import normalize_legacy_phone
from app.db.migrations import add_column, column_names, index_exists

logger = get_logger(__name__)

NEW_TABLES = [
    """CREATE TABLE IF NOT EXISTS pending_registrations (
        id INTEGER NOT NULL PRIMARY KEY,
        email VARCHAR(100) NOT NULL UNIQUE,
        full_name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        organization VARCHAR(100),
        password_hash VARCHAR(255) NOT NULL,
        created_at DATETIME NOT NULL,
        expires_at DATETIME NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS email_otps (
        id INTEGER NOT NULL PRIMARY KEY,
        email VARCHAR(100) NOT NULL,
        purpose VARCHAR(30) NOT NULL,
        code_hash VARCHAR(128) NOT NULL,
        created_at DATETIME NOT NULL,
        expires_at DATETIME NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        consumed_at DATETIME,
        invalidated_at DATETIME,
        ip_address VARCHAR(64),
        CONSTRAINT ck_email_otps_purpose CHECK (purpose IN ('registration','verify_email','login','password_reset')))""",
    "CREATE INDEX IF NOT EXISTS ix_email_otps_email_purpose_created ON email_otps (email, purpose, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_email_otps_email_created ON email_otps (email, created_at)",
    """CREATE TABLE IF NOT EXISTS refresh_tokens (
        id INTEGER NOT NULL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
        token_hash VARCHAR(128) NOT NULL UNIQUE,
        family_id VARCHAR(64) NOT NULL,
        created_at DATETIME NOT NULL,
        expires_at DATETIME NOT NULL,
        revoked_at DATETIME,
        replaced_by_id INTEGER,
        user_agent VARCHAR(255),
        ip_address VARCHAR(64))""",
    "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_family_id ON refresh_tokens (family_id)",
    """CREATE TABLE IF NOT EXISTS revoked_access_tokens (
        jti VARCHAR(64) NOT NULL PRIMARY KEY,
        expires_at DATETIME NOT NULL)""",
    "CREATE INDEX IF NOT EXISTS ix_revoked_access_tokens_expires_at ON revoked_access_tokens (expires_at)",
    """CREATE TABLE IF NOT EXISTS complaint_events (
        id INTEGER NOT NULL PRIMARY KEY,
        complaint_id INTEGER NOT NULL REFERENCES complaints (id) ON DELETE CASCADE,
        actor_id INTEGER REFERENCES users (id) ON DELETE SET NULL,
        actor_role VARCHAR(20),
        event_type VARCHAR(50) NOT NULL,
        from_status VARCHAR(30),
        to_status VARCHAR(30),
        note TEXT,
        created_at DATETIME NOT NULL)""",
    "CREATE INDEX IF NOT EXISTS ix_complaint_events_complaint_id ON complaint_events (complaint_id)",
    "CREATE INDEX IF NOT EXISTS ix_complaint_events_created_at ON complaint_events (created_at)",
    """CREATE TABLE IF NOT EXISTS complaint_attachments (
        id INTEGER NOT NULL PRIMARY KEY,
        complaint_id INTEGER NOT NULL REFERENCES complaints (id) ON DELETE CASCADE,
        uploaded_by INTEGER REFERENCES users (id) ON DELETE SET NULL,
        filename VARCHAR(255) NOT NULL,
        content_type VARCHAR(100) NOT NULL,
        size_bytes INTEGER NOT NULL,
        sha256 VARCHAR(64) NOT NULL,
        data BLOB NOT NULL,
        created_at DATETIME NOT NULL)""",
    "CREATE INDEX IF NOT EXISTS ix_complaint_attachments_complaint_id ON complaint_attachments (complaint_id)",
    """CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER NOT NULL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
        type VARCHAR(50) NOT NULL,
        title VARCHAR(200) NOT NULL,
        message TEXT NOT NULL,
        ticket_id VARCHAR(50),
        is_read BOOLEAN NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL,
        read_at DATETIME)""",
    "CREATE INDEX IF NOT EXISTS ix_notifications_user_read ON notifications (user_id, is_read, created_at)",
    """CREATE TABLE IF NOT EXISTS ai_execution_logs (
        id INTEGER NOT NULL PRIMARY KEY,
        complaint_id INTEGER REFERENCES complaints (id) ON DELETE SET NULL,
        operation VARCHAR(50) NOT NULL,
        provider VARCHAR(50),
        model VARCHAR(120),
        success BOOLEAN NOT NULL DEFAULT 1,
        fallback_used BOOLEAN NOT NULL DEFAULT 0,
        latency_ms INTEGER,
        error VARCHAR(500),
        created_at DATETIME NOT NULL)""",
    "CREATE INDEX IF NOT EXISTS ix_ai_execution_logs_complaint_id ON ai_execution_logs (complaint_id)",
    "CREATE INDEX IF NOT EXISTS ix_ai_execution_logs_created_at ON ai_execution_logs (created_at)",
]


class MigrationAbort(RuntimeError):
    pass


def _upgrade_users(conn) -> None:
    cols = column_names(conn, "users")

    clashes = conn.execute(text(
        "SELECT lower(trim(email)) AS e, COUNT(*) FROM users GROUP BY e HAVING COUNT(*) > 1"
    )).fetchall()
    if clashes:
        raise MigrationAbort(
            f"{len(clashes)} email address(es) differ only by case/whitespace. Merge those accounts "
            "manually before running this migration."
        )
    conn.execute(text("UPDATE users SET email = lower(trim(email)) WHERE email != lower(trim(email))"))

    if "job_title" not in cols:
        conn.execute(text("ALTER TABLE users RENAME COLUMN role TO job_title"))
    add_column(conn, "users", "role",
               "VARCHAR(20) NOT NULL DEFAULT 'customer' CONSTRAINT ck_users_role CHECK (role IN ('customer','agent','admin'))")

    legacy_admins = conn.execute(text("SELECT COUNT(*) FROM users WHERE job_title = 'Admin'")).scalar()
    if "is_agent" in column_names(conn, "users"):
        conn.execute(text("UPDATE users SET role = 'agent' WHERE is_agent = 1"))
    # "Admin" was an authorization flag masquerading as a title; it grants nothing now.
    conn.execute(text("UPDATE users SET job_title = NULL WHERE job_title = 'Admin'"))
    if legacy_admins:
        logger.warning(
            "%s account(s) previously had role 'Admin'. Admin access is no longer granted by data in "
            "that column. Provision admins with: python -m app.cli promote --email <email> --role admin",
            legacy_admins,
        )

    add_column(conn, "users", "email_verified", "BOOLEAN NOT NULL DEFAULT 0")
    add_column(conn, "users", "email_verified_at", "DATETIME")
    add_column(conn, "users", "department", "VARCHAR(50)")
    add_column(conn, "users", "token_version", "INTEGER NOT NULL DEFAULT 0")
    add_column(conn, "users", "failed_login_attempts", "INTEGER NOT NULL DEFAULT 0")
    add_column(conn, "users", "locked_until", "DATETIME")
    add_column(conn, "users", "last_login_at", "DATETIME")
    add_column(conn, "users", "updated_at", "DATETIME")
    add_column(conn, "users", "legacy_phone", "VARCHAR(40)")

    # Normalise phones; keep anything unusable in legacy_phone rather than deleting it.
    seen = set()
    rows = conn.execute(text("SELECT id, phone FROM users WHERE phone IS NOT NULL ORDER BY id")).fetchall()
    for user_id, raw in rows:
        normalized = normalize_legacy_phone(raw)
        if normalized and normalized not in seen:
            seen.add(normalized)
            if normalized != raw:
                conn.execute(text("UPDATE users SET phone = :p WHERE id = :i"), {"p": normalized, "i": user_id})
        else:
            conn.execute(
                text("UPDATE users SET legacy_phone = :raw, phone = NULL WHERE id = :i"),
                {"raw": (raw or "")[:40] or None, "i": user_id},
            )

    for legacy in ("otp", "otp_expiry", "is_agent"):
        if legacy in column_names(conn, "users"):
            conn.execute(text(f"ALTER TABLE users DROP COLUMN {legacy}"))

    if not index_exists(conn, "uq_users_phone"):
        conn.execute(text("CREATE UNIQUE INDEX uq_users_phone ON users (phone) WHERE phone IS NOT NULL"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_role ON users (role)"))


def _upgrade_complaints(conn) -> None:
    add_column(conn, "complaints", "user_id", "INTEGER REFERENCES users (id) ON DELETE SET NULL")
    add_column(
        conn, "complaints", "status",
        "VARCHAR(30) NOT NULL DEFAULT 'open' CONSTRAINT ck_complaints_status "
        "CHECK (status IN ('open','in_progress','awaiting_approval','resolved','closed'))",
    )
    add_column(conn, "complaints", "assigned_agent_id", "INTEGER REFERENCES users (id) ON DELETE SET NULL")
    add_column(conn, "complaints", "assigned_at", "DATETIME")
    add_column(conn, "complaints", "requires_human_review", "BOOLEAN NOT NULL DEFAULT 0")
    add_column(conn, "complaints", "review_reason", "VARCHAR(255)")
    add_column(conn, "complaints", "ai_provider", "VARCHAR(50)")
    add_column(conn, "complaints", "ai_model", "VARCHAR(120)")
    add_column(conn, "complaints", "ai_latency_ms", "INTEGER")
    add_column(conn, "complaints", "ai_fallback_used", "BOOLEAN NOT NULL DEFAULT 0")
    add_column(conn, "complaints", "resolved_at", "DATETIME")

    conn.execute(text(
        "UPDATE complaints SET user_id = (SELECT u.id FROM users u WHERE u.email = lower(trim(complaints.email))) "
        "WHERE user_id IS NULL"
    ))
    conn.execute(text(
        "UPDATE complaints SET status = 'resolved', resolved_at = COALESCE(resolved_at, updated_at) "
        "WHERE is_resolved = 1 AND status = 'open'"
    ))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_complaints_user_id ON complaints (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_complaints_status ON complaints (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_complaints_assigned_agent_id ON complaints (assigned_agent_id)"))


def _upgrade_resolutions(conn) -> None:
    add_column(conn, "agent_resolutions", "requires_approval", "BOOLEAN NOT NULL DEFAULT 0")
    add_column(conn, "agent_resolutions", "approved_by_id", "INTEGER REFERENCES users (id) ON DELETE SET NULL")
    add_column(conn, "agent_resolutions", "approved_at", "DATETIME")


def upgrade(conn) -> None:
    _upgrade_users(conn)
    _upgrade_complaints(conn)
    _upgrade_resolutions(conn)
    for ddl in NEW_TABLES:
        conn.execute(text(ddl))
    # Seed history so existing tickets have a timeline.
    conn.execute(text(
        "INSERT INTO complaint_events (complaint_id, actor_id, actor_role, event_type, to_status, note, created_at) "
        "SELECT c.id, c.user_id, 'customer', 'created', 'open', 'Imported from pre-migration data', "
        "COALESCE(c.created_at, CURRENT_TIMESTAMP) FROM complaints c "
        "WHERE NOT EXISTS (SELECT 1 FROM complaint_events e WHERE e.complaint_id = c.id)"
    ))
