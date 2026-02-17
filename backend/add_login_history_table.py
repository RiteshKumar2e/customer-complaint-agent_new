"""
Database migration script to add login_history table
Run this script to create the login_history table in the database
"""

from app.db.database import engine, Base
from app.db.models import User, LoginHistory, Complaint

def migrate():
    """Create all tables including the new login_history table"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Login history table created successfully!")
    print("✅ All tables are up to date!")

if __name__ == "__main__":
    migrate()
