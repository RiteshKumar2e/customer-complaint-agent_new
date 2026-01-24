import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

def get_ist_time():
    """Helper to get current time in IST (UTC+5:30)"""
    return datetime.utcnow() + timedelta(hours=5, minutes=30)


# ✅ Read DATABASE_URL from environment (Render / Local)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///complaints.db")

# ✅ Render uses 'postgres://' which SQLAlchemy requires 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
# ✅ Fix MySQL/MariaDB driver
elif DATABASE_URL.startswith("mysql://"):
    # Ensure we use pymysql for MySQL/MariaDB connections
    if "pymysql" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")



# ✅ Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
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
    
    new_columns = [
        ("bio", "TEXT"),
        ("role", "VARCHAR(100) DEFAULT 'Strategic Member'"),
        ("location", "VARCHAR(100) DEFAULT 'India'"),
        ("ai_analysis_steps", "TEXT"),
        ("user_rating", "INTEGER"),
        ("user_feedback", "TEXT"),
        ("subject", "VARCHAR(255)"),
        ("description", "TEXT"),
        ("user_resolution_feedback", "BOOLEAN"),
        ("user_resolution_comment", "TEXT")
    ]
    
    with engine.connect() as conn:
        # Migration for 'users' table
        for col_name, col_type in new_columns[:3]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()

        # Migration for 'complaints' table
        for col_name, col_type in new_columns[3:]:
            try:
                conn.execute(text(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"))
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
