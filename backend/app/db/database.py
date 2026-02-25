import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

def get_ist_time():
    """Helper to get current time in IST (UTC+5:30)"""
    return datetime.utcnow() + timedelta(hours=5, minutes=30)


# ✅ Read DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///complaints.db")

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

# ✅ Create engine with SSL support for Aiven if needed
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "aivencloud.com" in DATABASE_URL:
    # Aiven requires SSL, but we must pass it via connect_args for pymysql
    connect_args = {"ssl": {"ca": None}} # This triggers standard SSL check for Aiven

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args
)

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
