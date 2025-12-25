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

def set_admin(email):
    print(f"🚀 Connecting to database to set {email} as Admin...")
    
    with engine.connect() as conn:
        try:
            # Check if user exists
            result = conn.execute(text("SELECT email FROM users WHERE email = :email"), {"email": email}).fetchone()
            
            if not result:
                print(f"❌ User with email {email} not found. Please register first.")
                return

            # Update role to Admin
            conn.execute(
                text("UPDATE users SET role = 'Admin' WHERE email = :email"),
                {"email": email}
            )
            conn.commit()
            print(f"✅ Successfully set {email} as Admin!")
            print("✨ You can now access the Admin Panel after logging in.")
            
        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        set_admin(sys.argv[1])
    else:
        email = input("Enter user email to set as Admin: ")
        set_admin(email)
