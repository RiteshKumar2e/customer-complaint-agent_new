
import sqlite3
import os

db_path = "backend/complaints.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if ticket_id exists
        cursor.execute("PRAGMA table_info(complaints)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "ticket_id" not in columns:
            print("🚀 Adding ticket_id column to complaints table...")
            cursor.execute("ALTER TABLE complaints ADD COLUMN ticket_id VARCHAR(50)")
            conn.commit()
            print("✅ Column added successfully!")
        else:
            print("ℹ️ ticket_id column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error migrating database: {str(e)}")
