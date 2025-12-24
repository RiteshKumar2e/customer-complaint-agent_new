from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string
from passlib.context import CryptContext
from app.db.database import get_db
from app.db.models import User
from app.schemas.user import (
    UserCreate, UserLogin, PasswordLogin, ForgotPassword, 
    ResetPassword, OTPVerify, UserResponse, Token, GoogleAuth
)
from app.services.email_service import email_service
from jose import jwt
import os

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-keep-it-safe")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_otp():
    return "".join(random.choices(string.digits, k=6))

def generate_reset_token():
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password if provided
    hashed_pwd = None
    if user_data.password:
        hashed_pwd = get_password_hash(user_data.password)
        
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_pwd,
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

@router.post("/google")
def google_auth(data: GoogleAuth, db: Session = Depends(get_db)):
    """
    Step 1: Google Sign-In - Send OTP to the authenticated Google email
    """
    # In a real app, verify the Google token here using google-auth library
    # For now, we'll assume the frontend sends a valid email from Google OAuth
    email = data.token  # Simplified: frontend sends email as token for demo
    
    # Check if user exists, if not create a new user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, full_name=data.name or "Google User", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate and send OTP
    otp = generate_otp()
    user.otp = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    email_service.send_otp(user.email, otp)
    return {
        "message": "OTP sent to your Google email",
        "email": email,
        "requires_otp": True
    }

@router.post("/google-verify-otp", response_model=Token)
def google_verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    """
    Step 2: Verify OTP sent to Google email and complete sign-in
    """
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

@router.post("/login-password", response_model=Token)
def login_with_password(data: PasswordLogin, db: Session = Depends(get_db)):
    """
    Login with email and password
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="User not found. Please register first."
        )
    
    if not user.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="No password set. Please use Google Sign-In or set a password."
        )
    
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Password is wrong. Try forgot password to reset it."
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    """
    Send password reset link to user's email
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # Don't reveal if user exists or not for security
        return {"message": "If your email is registered, you will receive a password reset link."}
    
    # Generate reset token
    reset_token = generate_reset_token()
    user.otp = reset_token  # Reuse OTP field for reset token
    user.otp_expiry = datetime.utcnow() + timedelta(hours=1)  # 1 hour validity
    db.commit()
    
    # Send reset email
    email_service.send_password_reset(user.email, user.full_name or "User", reset_token)
    
    return {"message": "If your email is registered, you will receive a password reset link."}

@router.post("/reset-password")
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """
    Reset password using the reset token from email
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    
    if user.otp != data.reset_token:
        raise HTTPException(status_code=400, detail="Invalid reset link")
    
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="Reset link expired. Please request a new one.")
    
    # Update password
    user.hashed_password = get_password_hash(data.new_password)
    user.otp = None
    user.otp_expiry = None
    db.commit()
    
    return {"message": "Password reset successfully. You can now login with your new password."}
