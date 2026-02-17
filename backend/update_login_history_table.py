"""
Database migration script to update login_history table with new columns
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = "sqlite:///./customer_complaint.db" # Adjusted for SQLite default

def migrate():
    engine = create_engine(DATABASE_URL)
    columns = [
        ("user_name", "VARCHAR(100)"),
        ("logout_time", "DATETIME"),
        ("device_type", "VARCHAR(100)"),
        ("status", "VARCHAR(50)"),
        ("login_location", "VARCHAR(255)"),
        ("created_at", "DATETIME")
    ]
    
    with engine.connect() as conn:
        print("Checking for existing table...")
        for col_name, col_type in columns:
            try:
                print(f"Adding column {col_name}...")
                conn.execute(text(f"ALTER TABLE login_history ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"✅ Added {col_name}")
            except Exception as e:
                print(f"⚠️ Could not add {col_name} (it might already exist): {e}")

    print("✅ Migration completed!")

if __name__ == "__main__":
    migrate()
