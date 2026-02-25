import os
import sys
from sqlalchemy import create_engine, MetaData, Table, select, insert
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate():
    # 1. Setup Source (Current DB)
    SOURCE_URL = os.getenv("DATABASE_URL")
    if not SOURCE_URL:
        print("❌ Error: DATABASE_URL not found in .env")
        return

    # 2. Setup Destination (Turso DB)
    # The user should add TURSO_DATABASE_URL to their .env for this script
    DEST_URL = os.getenv("TURSO_DATABASE_URL")
    if not DEST_URL:
        print("❌ Error: TURSO_DATABASE_URL not found in .env")
        print("ℹ️ Please add TURSO_DATABASE_URL=libsql://... to your .env file")
        return

    # Fix drivers for SQLAlchemy
    if SOURCE_URL.startswith("mysql://") and "pymysql" not in SOURCE_URL:
        SOURCE_URL = SOURCE_URL.replace("mysql://", "mysql+pymysql://")
    
    if DEST_URL.startswith("libsql://"):
        DEST_URL = DEST_URL.replace("libsql://", "sqlite+libsql://")

    print(f"🔄 Starting migration...")
    print(f"📡 Source: {SOURCE_URL.split('@')[-1]}") # Print only host for safety
    print(f"🎯 Destination: {DEST_URL.split('?')[0]}")

    try:
        source_engine = create_engine(SOURCE_URL)
        dest_engine = create_engine(DEST_URL)
        
        source_metadata = MetaData()
        source_metadata.reflect(bind=source_engine)
        
        # Create tables in destination if they don't exist
        print("🏗️ Creating tables in destination...")
        source_metadata.create_all(bind=dest_engine)
        
        # Migrate data table by table
        for table_name in source_metadata.tables:
            print(f"📦 Migrating table: {table_name}...")
            
            table = Table(table_name, source_metadata, autoload_with=source_engine)
            
            with source_engine.connect() as s_conn:
                rows = s_conn.execute(select(table)).fetchall()
                
                if not rows:
                    print(f"  - Table {table_name} is empty, skipping.")
                    continue
                
                # Insert in chunks to avoid memory issues
                with dest_engine.connect() as d_conn:
                    # Optional: Clear destination table first if needed
                    # d_conn.execute(table.delete())
                    
                    data = [dict(row._mapping) for row in rows]
                    d_conn.execute(insert(table), data)
                    d_conn.commit()
                    
            print(f"  ✅ Migrated {len(rows)} rows from {table_name}")

        print("\n✨ Migration Successful!")
        print("🚀 You can now update your DATABASE_URL in Render to your Turso URL.")

    except Exception as e:
        print(f"\n❌ Migration Failed: {str(e)}")
        if "libsql" in str(e).lower():
            print("💡 Make sure you have installed 'libsql-client' and 'sqlalchemy-libsql'")

if __name__ == "__main__":
    migrate()
