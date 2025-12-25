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
# ✅ Fix MySQL driver if needed
elif DATABASE_URL.startswith("mysql://"):
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
        ("location", "VARCHAR(100) DEFAULT 'India'")
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in new_columns:
            try:
                # SQLite and Postgres have different ALTER TABLE syntax but this works for simple column additions
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"✅ Added missing column: {col_name}")
            except Exception as e:
                # Ignore errors if column already exists
                error_str = str(e).lower()
                if "already exists" in error_str or "duplicate column" in error_str:
                    pass
                else:
                    print(f"⚠️ Note on column {col_name}: {e}")
