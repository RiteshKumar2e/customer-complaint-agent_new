from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string
from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserLogin, OTPVerify, UserResponse, Token, GoogleAuth
from app.services.email_service import email_service
from jose import jwt
import os

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-keep-it-safe")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_otp():
    return "".join(random.choices(string.digits, k=6))

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/request-otp")
def request_otp(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # If user doesn't exist, we might want to register them automatically or return error
        # Requirement says: "if not id is present got to register page"
        # So backend should probably just return 404
        raise HTTPException(status_code=404, detail="User not found. Please register first.")
    
    otp = generate_otp()
    user.otp = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    email_service.send_otp(user.email, otp)
    return {"message": "OTP sent to your email"}

@router.post("/verify-otp", response_model=Token)
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.otp:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if user.otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")
    
    # Clear OTP
    user.otp = None
    user.otp_expiry = None
    db.commit()
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }

@router.post("/google", response_model=Token)
def google_auth(data: GoogleAuth, db: Session = Depends(get_db)):
    # In a real app, verify the Google token here using google-auth library
    # For now, we'll assume the frontend sends a valid email since we can't easily verify without client IDs
    # This is a simplified version
    email = data.token # Simplified: frontend sends email as token for demo
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, full_name="Google User", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }
