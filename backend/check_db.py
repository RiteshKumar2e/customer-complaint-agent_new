import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database():
    # Use the same logic as your app to get the DB URL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///complaints.db")
    
    # Fix for Render/PostgreSQL
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    elif DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")

    print(f"🔍 Connecting to: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # Check Users
            print("\n👥 --- USERS ---")
            users_result = connection.execute(text("SELECT id, full_name, email FROM users"))
            users = users_result.fetchall()
            if not users:
                print("No users found.")
            for user in users:
                print(f"ID: {user[0]} | Name: {user[1]} | Email: {user[2]}")

            # Check Complaints
            print("\n📋 --- COMPLAINTS ---")
            complaints_result = connection.execute(text("SELECT ticket_id, category, priority, email FROM complaints ORDER BY id DESC LIMIT 5"))
            complaints = complaints_result.fetchall()
            if not complaints:
                print("No complaints found.")
            for comp in complaints:
                print(f"Ticket: {comp[0]} | {comp[1]} | {comp[2]} | By: {comp[3]}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database()
