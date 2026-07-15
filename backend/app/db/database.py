import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

def get_ist_time():
    """Helper to get current time in IST (UTC+5:30)"""
    return datetime.utcnow() + timedelta(hours=5, minutes=30)


# ✅ Read the database URL from environment.
# TURSO_DATABASE_URL is accepted as an alias so a Turso-only deployment works
# without duplicating the same value under two names.
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("TURSO_DATABASE_URL") or ""

# A local SQLite file is fine for development, but on a host with an ephemeral
# filesystem (Render, Docker without a volume) it is silently wiped on every
# restart, so every complaint written to it is lost. Refuse to start that way
# instead of pretending the writes succeeded.
IS_HOSTED = bool(os.getenv("RENDER") or os.getenv("ENVIRONMENT") == "production")
if not DATABASE_URL:
    if IS_HOSTED:
        raise RuntimeError(
            "No DATABASE_URL (or TURSO_DATABASE_URL) is set. Refusing to fall back to "
            "local SQLite: this host's filesystem is ephemeral and all data would be "
            "lost on the next restart. Set DATABASE_URL to your Turso libsql:// URL."
        )
    DATABASE_URL = "sqlite:///complaints.db"
    print("[db] WARNING: No DATABASE_URL set. Using local SQLite file 'complaints.db' (development only).")

# ✅ Handle Render/Postgres URL conversion
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ✅ Handle MariaDB/MySQL (Aiven) URL conversion
elif DATABASE_URL.startswith("mysql://"):
    # Fix driver
    if "pymysql" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")

    # Strip 'ssl-mode=REQUIRED' if present to avoid TypeError
    if "ssl-mode=" in DATABASE_URL:
        import re
        DATABASE_URL = re.sub(r'[?&]ssl-mode=[^&]+', '', DATABASE_URL)

# ✅ Handle Turso (libsql) URL conversion
elif DATABASE_URL.startswith("libsql://"):
    DATABASE_URL = DATABASE_URL.replace("libsql://", "sqlite+libsql://", 1)
    # sqlalchemy-libsql picks its transport from this flag: secure=true -> https,
    # otherwise plain http, which a TLS-only Turso host rejects.
    if "secure=" not in DATABASE_URL:
        DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "secure=true"

    # sqlalchemy-libsql ships no Windows wheel, so a dev machine can't talk to
    # Turso at all. Fall back to SQLite there rather than refusing to boot, but
    # never on the deployed host, where that would silently lose every write.
    try:
        import sqlalchemy_libsql  # noqa: F401
    except ImportError:
        if IS_HOSTED:
            raise RuntimeError(
                "DATABASE_URL points at Turso but sqlalchemy-libsql is not installed. "
                "Install it (>=0.2.0) so writes reach Turso instead of a disposable file."
            )
        DATABASE_URL = "sqlite:///complaints.db"
        print(
            "[db] WARNING: sqlalchemy-libsql is unavailable (no Windows wheel). "
            "Falling back to local SQLite 'complaints.db'. This machine is NOT "
            "reading or writing Turso."
        )

# Covers plain sqlite:// and Turso's sqlite+libsql://, which share the pysqlite
# dialect's connect arguments and pooling behaviour.
IS_SQLITE_FAMILY = DATABASE_URL.startswith("sqlite")

# ✅ Create engine with SSL support for Aiven if needed
connect_args = {}
if IS_SQLITE_FAMILY:
    connect_args = {"check_same_thread": False}
elif "aivencloud.com" in DATABASE_URL:
    # Aiven requires SSL, but we must pass it via connect_args for pymysql
    connect_args = {"ssl": {"ca": None}} # This triggers standard SSL check for Aiven

# QueuePool sizing applies to the server-based backends; the sqlite dialects use
# their own pool class and reject these arguments.
pool_kwargs = {} if IS_SQLITE_FAMILY else {"pool_size": 10, "max_overflow": 20}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
    **pool_kwargs
)

print(f"[db] Backend: {DATABASE_URL.split('://')[0]} @ {DATABASE_URL.split('@')[-1].split('?')[0]}")

# ✅ Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ✅ Base
Base = declarative_base()

# ✅ Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_migrations():
    """Add missing columns to existing tables if they don't exist"""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Migration for 'users' table
        user_columns = [
            ("bio", "TEXT"),
            ("role", "VARCHAR(100) DEFAULT 'Strategic Member'"),
            ("location", "VARCHAR(100) DEFAULT 'India'"),
            ("is_agent", "BOOLEAN DEFAULT FALSE")
        ]
        for col_name, col_type in user_columns:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()

        # Migration for 'complaints' table
        complaint_columns = [
            ("ai_analysis_steps", "TEXT"),
            ("user_rating", "INTEGER"),
            ("user_feedback", "TEXT"),
            ("subject", "VARCHAR(255)"),
            ("description", "TEXT"),
            ("user_resolution_feedback", "BOOLEAN"),
            ("user_resolution_comment", "TEXT"),
            ("sentiment_score", "FLOAT DEFAULT 0")
        ]
        for col_name, col_type in complaint_columns:
            try:
                conn.execute(text(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()

        # Migration for 'login_history' table
        history_columns = [
            ("user_name", "VARCHAR(100)"),
            ("logout_time", "DATETIME"),
            ("device_type", "VARCHAR(100)"),
            ("status", "VARCHAR(50)"),
            ("login_location", "VARCHAR(255)"),
            ("created_at", "DATETIME"),
            ("phone", "VARCHAR(20)")
        ]
        for col_name, col_type in history_columns:
            try:
                conn.execute(text(f"ALTER TABLE login_history ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()

        # Migration for 'agent_resolutions' table
        agent_res_columns = [
            ("steps", "TEXT")
        ]
        for col_name, col_type in agent_res_columns:
            try:
                conn.execute(text(f"ALTER TABLE agent_resolutions ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()

        # ✅ Ensure complaint_text is nullable for legacy compatibility
        try:
            conn.execute(text("ALTER TABLE complaints ALTER COLUMN complaint_text DROP NOT NULL"))
            conn.commit()
        except Exception:
            try:
                # SQLite doesn't support ALTER COLUMN DROP NOT NULL, skip it there
                conn.rollback()
            except: pass
        
        # ✅ Manual fallback if Postgres/MySQL fails
        admin_email = "riteshkumar90359@gmail.com"
        try:
            conn.execute(
                text("UPDATE users SET role = 'Admin', full_name = 'Ritesh Kumar' WHERE email = :email"),
                {"email": admin_email}
            )
            conn.commit()
            print(f"👑 Admin role verified for: {admin_email}")
        except Exception as e:
            conn.rollback() # 🔄 Rollback here too
            print(f"⚠️ Could not set auto-admin: {e}")
