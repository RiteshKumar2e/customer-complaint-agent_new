"""
Database Migration Script for Agent Module
Adds new tables: agent_resolutions, model_validations, agent_audit_logs
Adds is_agent field to users table
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "mysql://root@127.0.0.1:3306/quickfix_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def migrate_agent_module():
    """Run migration for Agent Module"""
    db = SessionLocal()
    
    try:
        print("🚀 Starting Agent Module Migration...")
        
        # 1. Add is_agent column to users table
        print("\n📝 Step 1: Adding is_agent column to users table...")
        try:
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_agent BOOLEAN DEFAULT FALSE AFTER is_active
            """))
            db.commit()
            print("✅ Added is_agent column to users table")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("⚠️  is_agent column already exists, skipping...")
            else:
                raise e
        
        # 2. Create agent_resolutions table
        print("\n📝 Step 2: Creating agent_resolutions table...")
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_resolutions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    complaint_id INT NOT NULL,
                    ticket_id VARCHAR(50) NOT NULL,
                    agent_id INT NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    draft_solution TEXT,
                    final_solution TEXT NOT NULL,
                    validation_results JSON,
                    confidence_score FLOAT,
                    validation_status VARCHAR(50) DEFAULT 'pending',
                    model_agreement_metrics JSON,
                    resolution_timestamp DATETIME,
                    status VARCHAR(50) DEFAULT 'draft',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_complaint_id (complaint_id),
                    INDEX idx_ticket_id (ticket_id),
                    INDEX idx_agent_id (agent_id),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
                    FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            db.commit()
            print("✅ Created agent_resolutions table")
        except Exception as e:
            if "already exists" in str(e):
                print("⚠️  agent_resolutions table already exists, skipping...")
            else:
                raise e
        
        # 3. Create model_validations table
        print("\n📝 Step 3: Creating model_validations table...")
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS model_validations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    resolution_id INT NOT NULL,
                    model_name VARCHAR(100) NOT NULL,
                    validation_type VARCHAR(50) NOT NULL,
                    score FLOAT NOT NULL,
                    feedback TEXT,
                    passed BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_resolution_id (resolution_id),
                    FOREIGN KEY (resolution_id) REFERENCES agent_resolutions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            db.commit()
            print("✅ Created model_validations table")
        except Exception as e:
            if "already exists" in str(e):
                print("⚠️  model_validations table already exists, skipping...")
            else:
                raise e
        
        # 4. Create agent_audit_logs table
        print("\n📝 Step 4: Creating agent_audit_logs table...")
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_audit_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    agent_id INT NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    complaint_id INT,
                    ticket_id VARCHAR(50),
                    details JSON,
                    ip_address VARCHAR(50),
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_agent_id (agent_id),
                    INDEX idx_ticket_id (ticket_id),
                    INDEX idx_timestamp (timestamp),
                    FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            db.commit()
            print("✅ Created agent_audit_logs table")
        except Exception as e:
            if "already exists" in str(e):
                print("⚠️  agent_audit_logs table already exists, skipping...")
            else:
                raise e
        
        # 5. Grant agent access to admin users
        print("\n📝 Step 5: Granting agent access to admin users...")
        result = db.execute(text("""
            UPDATE users 
            SET is_agent = TRUE 
            WHERE role = 'Admin'
        """))
        db.commit()
        print(f"✅ Granted agent access to {result.rowcount} admin users")
        
        print("\n🎉 Agent Module Migration Completed Successfully!")
        print("\n📊 Summary:")
        print("   ✓ Added is_agent column to users table")
        print("   ✓ Created agent_resolutions table")
        print("   ✓ Created model_validations table")
        print("   ✓ Created agent_audit_logs table")
        print("   ✓ Granted agent access to admin users")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    migrate_agent_module()
