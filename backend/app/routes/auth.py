from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string
import hashlib
from passlib.context import CryptContext
from app.db.database import get_db, get_ist_time
from app.db.models import User, LoginHistory
from app.schemas.user import (
    UserCreate, UserLogin, PasswordLogin, ForgotPassword, 
    ResetPassword, OTPVerify, UserResponse, Token, GoogleAuth, UserUpdate
)
from app.services.email_service import email_service
import jwt
import os

router = APIRouter(prefix="/auth", tags=["auth"])

# Helper function to log login attempts
def log_login_attempt(db: Session, user_id: int, email: str, method: str, 
                     success: bool = True, failure_reason: str = None,
                     ip_address: str = None, user_agent: str = None,
                     user_name: str = None, login_location: str = None):
    """Log user login attempt for admin tracking"""
    # Simple device type detection
    ua = (user_agent or "").lower()
    device_type = "Desktop"
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        device_type = "Mobile"
    elif "tablet" in ua or "ipad" in ua:
        device_type = "Tablet"
    
    # Fetch phone from user model if not provided
    user = db.query(User).filter(User.id == user_id).first()
    phone = user.phone if user else None
        
    login_record = LoginHistory(
        user_id=user_id,
        user_name=user_name or email.split('@')[0],
        email=email,
        phone=phone,
        login_method=method,
        success=success,
        failure_reason=failure_reason,
        ip_address=ip_address,
        user_agent=user_agent,
        device_type=device_type,
        status="Completed" if success else "Failed",
        login_location=login_location or "India" # Use precise location if available
    )
    db.add(login_record)
    db.commit()

@router.post("/logout")
def logout(email: str, db: Session = Depends(get_db)):
    """Record user logout time"""
    last_login = db.query(LoginHistory).filter(
        LoginHistory.email == email,
        LoginHistory.success == True,
        LoginHistory.logout_time == None
    ).order_by(LoginHistory.login_time.desc()).first()
    
    if last_login:
        last_login.logout_time = get_ist_time()
        db.commit()
    
    return {"message": "Logged out successfully"}

# ... (rest of imports)

@router.patch("/update-profile", response_model=UserResponse)
def update_profile(email: str, data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone
    if data.organization is not None:
        user.organization = data.organization
    if data.profile_image is not None:
        user.profile_image = data.profile_image
    if data.bio is not None:
        user.bio = data.bio
    if data.role is not None:
        user.role = data.role
    if data.location is not None:
        user.location = data.location
        
    db.commit()
    db.refresh(user)
    return user


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-keep-it-safe")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 1. Try with SHA-256 pre-hash (new way - fixes 72-char limit)
    password_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    try:
        if pwd_context.verify(password_hash, hashed_password):
            return True
    except Exception:
        pass
        
    # 2. Fallback to plain password (old way) for existing users
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # Pre-hash with SHA-256 to bypass bcrypt 72-character limit
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password_hash)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = get_ist_time() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        phone=user_data.phone,
        organization=user_data.organization,
        profile_image=user_data.profile_image,
        hashed_password=hashed_pwd,
        is_active=True,
        role="Admin" if user_data.email == "riteshkumar90359@gmail.com" else "Strategic Member"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/request-otp")
def request_otp(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    
    # 🚀 AUTO-CREATE USER: If user doesn't exist, create them instantly for seamless OTP flow
    if not user:
        user = User(
            email=data.email,
            full_name=data.email.split('@')[0],  # Use email prefix as default name
            is_active=True,
            role="Admin" if data.email == "riteshkumar90359@gmail.com" else "Strategic Member"
        )
        db.add(user)
        db.flush()  # Get the user ID without committing yet
    
    # Generate and send OTP
    otp = generate_otp()
    user.otp = otp
    user.otp_expiry = get_ist_time() + timedelta(minutes=10)
    db.commit()
    
    # 🚀 INSTANT SEND: Fire-and-forget for maximum speed
    email_service.send_otp(user.email, otp)
    return {"message": "OTP sent to your email", "is_new_user": user.id is None}

@router.post("/verify-otp", response_model=Token)
def verify_otp(data: OTPVerify, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.otp:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if user.otp != data.otp:
        # Log failed OTP attempt
        log_login_attempt(
            db, user.id, user.email, "otp", 
            success=False, failure_reason="Invalid OTP",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            user_name=user.full_name,
            login_location=data.location
        )
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if get_ist_time() > user.otp_expiry:
        # Log expired OTP attempt
        log_login_attempt(
            db, user.id, user.email, "otp", 
            success=False, failure_reason="OTP expired",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            user_name=user.full_name,
            login_location=data.location
        )
        raise HTTPException(status_code=400, detail="OTP expired")
    
    # Clear OTP
    user.otp = None
    user.otp_expiry = None
    db.commit()
    
    # Log successful login
    log_login_attempt(
        db, user.id, user.email, "otp",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        user_name=user.full_name,
        login_location=data.location
    )
    
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
        user = User(
            email=email, 
            full_name=data.name or "Google User", 
            is_active=True,
            role="Admin" if email == "riteshkumar90359@gmail.com" else "Strategic Member"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate and send OTP
    otp = generate_otp()
    user.otp = otp
    user.otp_expiry = get_ist_time() + timedelta(minutes=10)
    db.commit()
    
    email_service.send_otp(user.email, otp)
    return {
        "message": "OTP sent to your Google email",
        "email": email,
        "requires_otp": True
    }

@router.post("/google-verify-otp", response_model=Token)
def google_verify_otp(data: OTPVerify, request: Request, db: Session = Depends(get_db)):
    """
    Step 2: Verify OTP sent to Google email and complete sign-in
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.otp:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if user.otp != data.otp:
        # Log failed Google OTP attempt
        log_login_attempt(
            db, user.id, user.email, "google", 
            success=False, failure_reason="Invalid OTP",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            user_name=user.full_name,
            login_location=data.location
        )
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if get_ist_time() > user.otp_expiry:
        # Log expired Google OTP attempt
        log_login_attempt(
            db, user.id, user.email, "google", 
            success=False, failure_reason="OTP expired",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            user_name=user.full_name,
            login_location=data.location
        )
        raise HTTPException(status_code=400, detail="OTP expired")
    
    # Clear OTP
    user.otp = None
    user.otp_expiry = None
    db.commit()
    
    # Log successful Google login
    log_login_attempt(
        db, user.id, user.email, "google",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        user_name=user.full_name,
        login_location=data.location
    )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }

@router.post("/login-password", response_model=Token)
def login_with_password(data: PasswordLogin, request: Request, db: Session = Depends(get_db)):
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
        # Log failed attempt - no password set
        log_login_attempt(
            db, user.id, user.email, "password", 
            success=False, failure_reason="No password set",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            user_name=user.full_name,
            login_location=data.location
        )
        raise HTTPException(
            status_code=400,
            detail="No password set. Please use Google Sign-In or set a password."
        )
    
    if not verify_password(data.password, user.hashed_password):
        # Log failed attempt - wrong password
        log_login_attempt(
            db, user.id, user.email, "password", 
            success=False, failure_reason="Wrong password",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            user_name=user.full_name,
            login_location=data.location
        )
        raise HTTPException(
            status_code=401,
            detail="Password is wrong. Try forgot password to reset it."
        )
    
    # Log successful password login
    log_login_attempt(
        db, user.id, user.email, "password",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        user_name=user.full_name,
        login_location=data.location
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
    user.otp_expiry = get_ist_time() + timedelta(hours=1)  # 1 hour validity
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
    
    if get_ist_time() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="Reset link expired. Please request a new one.")
    
    # Update password
    user.hashed_password = get_password_hash(data.new_password)
    user.otp = None
    user.otp_expiry = None
    db.commit()
    
    return {"message": "Password reset successfully. You can now login with your new password."}

# ===== ADMIN ENDPOINTS FOR LOGIN HISTORY =====

@router.get("/admin/login-history")
def get_login_history(
    email: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get login history for all users or a specific user (Admin only)
    Query params:
    - email: Filter by specific user email (optional)
    - limit: Number of records to return (default 100)
    """
    query = db.query(LoginHistory, User.full_name).outerjoin(User, LoginHistory.user_id == User.id)
    
    if email:
        query = query.filter(LoginHistory.email == email)
    
    results = query.order_by(LoginHistory.login_time.desc()).limit(limit).all()
    
    return {
        "total": len(results),
        "records": [
            {
                "id": record.id,
                "user_id": record.user_id,
                "user_name": record.user_name or full_name or record.email.split('@')[0], # Fallback to email name
                "email": record.email,
                "phone": record.phone,
                "login_method": record.login_method,
                "ip_address": record.ip_address,
                "user_agent": record.user_agent,
                "device_type": record.device_type,
                "login_location": record.login_location,
                "success": record.success,
                "status": record.status,
                "failure_reason": record.failure_reason,
                "login_time": record.login_time.isoformat() if record.login_time else None,
                "logout_time": record.logout_time.isoformat() if record.logout_time else None,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
            for record, full_name in results
        ]
    }

@router.get("/admin/login-stats")
def get_login_stats(db: Session = Depends(get_db)):
    """
    Get login statistics (Admin only)
    """
    from sqlalchemy import func
    
    total_logins = db.query(func.count(LoginHistory.id)).scalar()
    successful_logins = db.query(func.count(LoginHistory.id)).filter(LoginHistory.success == True).scalar()
    failed_logins = db.query(func.count(LoginHistory.id)).filter(LoginHistory.success == False).scalar()
    
    # Login methods breakdown
    method_stats = db.query(
        LoginHistory.login_method,
        func.count(LoginHistory.id).label('count')
    ).group_by(LoginHistory.login_method).all()
    
    # Recent failed attempts
    recent_failures = db.query(LoginHistory).filter(
        LoginHistory.success == False
    ).order_by(LoginHistory.login_time.desc()).limit(10).all()
    
    return {
        "total_logins": total_logins,
        "successful_logins": successful_logins,
        "failed_logins": failed_logins,
        "success_rate": round((successful_logins / total_logins * 100) if total_logins > 0 else 0, 2),
        "methods": {method: count for method, count in method_stats},
        "recent_failures": [
            {
                "email": record.email,
                "method": record.login_method,
                "reason": record.failure_reason,
                "time": record.login_time.isoformat() if record.login_time else None
            }
            for record in recent_failures
        ]
    }

@router.delete("/admin/login-history/{history_id}")
def delete_login_history(history_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific login history record (Admin only)
    """
    record = db.query(LoginHistory).filter(LoginHistory.id == history_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    db.delete(record)
    db.commit()
    return {"message": "Record deleted successfully"}

