import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Read DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///complaints.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
elif DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")

engine = create_engine(DATABASE_URL)

def migrate():
    print(f"🚀 Connecting to: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    
    with engine.connect() as conn:
        # Check current columns in users table
        try:
            print("🧐 Checking for missing columns...")
            
            # Use universal SQL to try adding columns if they don't exist
            # Note: SQLite and PostgreSQL differ, so we handle it gracefully
            
            new_columns = [
                ("bio", "TEXT"),
                ("role", "VARCHAR(100) DEFAULT 'Strategic Member'"),
                ("location", "VARCHAR(100) DEFAULT 'India'")
            ]
            
            for col_name, col_type in new_columns:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                        print(f"ℹ️ Column '{col_name}' already exists, skipping.")
                    else:
                        print(f"❌ Error adding '{col_name}': {e}")
            
            conn.commit()
            print("✨ Migration completed successfully!")
            
        except Exception as e:
            print(f"💥 Migration failed: {e}")

if __name__ == "__main__":
    migrate()
