"""
0001 — the schema as it existed in production before versioned migrations.

On the live Turso database every statement here is a no-op (tables already
exist; the old ad-hoc `run_migrations()` columns are added only if missing).
On a fresh database it recreates that legacy schema so 0002 can upgrade both
paths identically.
"""
from sqlalchemy import text

from app.db.migrations import add_column

LEGACY_DDL = [
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER NOT NULL, email VARCHAR(100) NOT NULL, full_name VARCHAR(100), phone VARCHAR(20),
        organization VARCHAR(100), profile_image TEXT, hashed_password VARCHAR(255), google_id VARCHAR(255),
        otp VARCHAR(255), otp_expiry DATETIME, is_active BOOLEAN, is_agent BOOLEAN, bio TEXT,
        role VARCHAR(100), location VARCHAR(100), created_at DATETIME, PRIMARY KEY (id))""",
    """CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER NOT NULL, ticket_id VARCHAR(50), name VARCHAR(100) NOT NULL, email VARCHAR(100) NOT NULL,
        subject VARCHAR(255), description TEXT, complaint_text TEXT, category VARCHAR(50) NOT NULL,
        priority VARCHAR(20) NOT NULL, sentiment VARCHAR(20), sentiment_score FLOAT, response TEXT,
        solution TEXT, satisfaction_prediction VARCHAR(20), action VARCHAR(255), similar_complaints TEXT,
        ai_analysis_steps TEXT, user_rating INTEGER, user_feedback TEXT, user_resolution_feedback BOOLEAN,
        user_resolution_comment TEXT, created_at DATETIME, updated_at DATETIME, is_resolved BOOLEAN,
        PRIMARY KEY (id))""",
    """CREATE TABLE IF NOT EXISTS login_history (
        id INTEGER NOT NULL, user_id INTEGER NOT NULL, user_name VARCHAR(100), email VARCHAR(100) NOT NULL,
        phone VARCHAR(20), login_method VARCHAR(50) NOT NULL, ip_address VARCHAR(50), user_agent TEXT,
        device_type VARCHAR(100), login_location VARCHAR(255), success BOOLEAN, status VARCHAR(50),
        failure_reason VARCHAR(255), login_time DATETIME, logout_time DATETIME, created_at DATETIME,
        PRIMARY KEY (id), FOREIGN KEY(user_id) REFERENCES users (id))""",
    """CREATE TABLE IF NOT EXISTS agent_resolutions (
        id INTEGER NOT NULL, complaint_id INTEGER NOT NULL, ticket_id VARCHAR(50) NOT NULL,
        agent_id INTEGER NOT NULL, agent_name VARCHAR(100) NOT NULL, draft_solution TEXT,
        final_solution TEXT NOT NULL, steps TEXT, validation_results JSON, confidence_score FLOAT,
        validation_status VARCHAR(50), model_agreement_metrics JSON, resolution_timestamp DATETIME,
        status VARCHAR(50), created_at DATETIME, updated_at DATETIME, PRIMARY KEY (id),
        FOREIGN KEY(complaint_id) REFERENCES complaints (id), FOREIGN KEY(agent_id) REFERENCES users (id))""",
    """CREATE TABLE IF NOT EXISTS model_validations (
        id INTEGER NOT NULL, resolution_id INTEGER NOT NULL, model_name VARCHAR(100) NOT NULL,
        validation_type VARCHAR(50) NOT NULL, score FLOAT NOT NULL, feedback TEXT, passed BOOLEAN,
        created_at DATETIME, PRIMARY KEY (id),
        FOREIGN KEY(resolution_id) REFERENCES agent_resolutions (id))""",
    """CREATE TABLE IF NOT EXISTS agent_audit_logs (
        id INTEGER NOT NULL, agent_id INTEGER NOT NULL, action VARCHAR(100) NOT NULL, complaint_id INTEGER,
        ticket_id VARCHAR(50), details JSON, ip_address VARCHAR(50), user_agent TEXT, timestamp DATETIME,
        PRIMARY KEY (id), FOREIGN KEY(agent_id) REFERENCES users (id))""",
]

LEGACY_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)",
    "CREATE INDEX IF NOT EXISTS ix_complaints_id ON complaints (id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_complaints_ticket_id ON complaints (ticket_id)",
    "CREATE INDEX IF NOT EXISTS ix_complaints_email ON complaints (email)",
    "CREATE INDEX IF NOT EXISTS ix_complaints_created_at ON complaints (created_at)",
    "CREATE INDEX IF NOT EXISTS ix_login_history_id ON login_history (id)",
    "CREATE INDEX IF NOT EXISTS ix_login_history_user_id ON login_history (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_login_history_email ON login_history (email)",
    "CREATE INDEX IF NOT EXISTS ix_login_history_login_time ON login_history (login_time)",
    "CREATE INDEX IF NOT EXISTS ix_agent_resolutions_id ON agent_resolutions (id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_resolutions_complaint_id ON agent_resolutions (complaint_id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_resolutions_ticket_id ON agent_resolutions (ticket_id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_resolutions_agent_id ON agent_resolutions (agent_id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_resolutions_created_at ON agent_resolutions (created_at)",
    "CREATE INDEX IF NOT EXISTS ix_model_validations_id ON model_validations (id)",
    "CREATE INDEX IF NOT EXISTS ix_model_validations_resolution_id ON model_validations (resolution_id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_audit_logs_id ON agent_audit_logs (id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_audit_logs_agent_id ON agent_audit_logs (agent_id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_audit_logs_ticket_id ON agent_audit_logs (ticket_id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_audit_logs_timestamp ON agent_audit_logs (timestamp)",
]

# Columns the pre-versioning `run_migrations()` added at runtime.
LEGACY_COLUMNS = {
    "users": [("bio", "TEXT"), ("role", "VARCHAR(100)"), ("location", "VARCHAR(100)"), ("is_agent", "BOOLEAN")],
    "complaints": [
        ("ai_analysis_steps", "TEXT"), ("user_rating", "INTEGER"), ("user_feedback", "TEXT"),
        ("subject", "VARCHAR(255)"), ("description", "TEXT"), ("user_resolution_feedback", "BOOLEAN"),
        ("user_resolution_comment", "TEXT"), ("sentiment_score", "FLOAT"),
    ],
    "login_history": [
        ("user_name", "VARCHAR(100)"), ("logout_time", "DATETIME"), ("device_type", "VARCHAR(100)"),
        ("status", "VARCHAR(50)"), ("login_location", "VARCHAR(255)"), ("created_at", "DATETIME"),
        ("phone", "VARCHAR(20)"),
    ],
    "agent_resolutions": [("steps", "TEXT")],
}


def upgrade(conn) -> None:
    for ddl in LEGACY_DDL:
        conn.execute(text(ddl))
    for table, columns in LEGACY_COLUMNS.items():
        for name, ddl in columns:
            add_column(conn, table, name, ddl)
    for ddl in LEGACY_INDEXES:
        conn.execute(text(ddl))
