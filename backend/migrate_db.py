"""
Database migration script to add new fields to users table
Run this to update your existing database schema
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'complaints.db')

def migrate_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add phone column if it doesn't exist
        if 'phone' not in columns:
            print("Adding 'phone' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
            print("✓ Added 'phone' column")
        
        # Add organization column if it doesn't exist
        if 'organization' not in columns:
            print("Adding 'organization' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN organization VARCHAR(100)")
            print("✓ Added 'organization' column")
        
        # Add profile_image column if it doesn't exist
        if 'profile_image' not in columns:
            print("Adding 'profile_image' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN profile_image VARCHAR(500)")
            print("✓ Added 'profile_image' column")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()
