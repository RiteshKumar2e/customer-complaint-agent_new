#!/usr/bin/env python
"""
Database initialization script
Run this to create all tables in the database
"""

import os
from app.db.database import engine, Base
from app.db.models import Complaint, User

def init_db():
    """Initialize database with all tables"""
    print("🗄️  Initializing database...")
    
    # Get database URL from environment or use default
    db_url = os.getenv("DATABASE_URL", "sqlite:///./complaints.db")
    print(f"📍 Using database: {db_url}")
    
    # Create all tables
    print("📝 Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")
    print("\nTables created:")
    print("  • complaints - Stores customer complaints and AI analysis")
    print("  • users - Stores user authentication data")
    
    # Print sample query
    print("\n📊 Sample query:")
    print("  SELECT * FROM complaints;")

if __name__ == "__main__":
    init_db()
