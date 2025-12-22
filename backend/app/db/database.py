import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Configuration (recommended for production)
# SQLite as fallback for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./complaints.db"  # Local SQLite for development
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Verify connection before using
    pool_size=10,            # Connection pool size
    max_overflow=20,         # Max overflow connections
    echo=False,              # Set True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
