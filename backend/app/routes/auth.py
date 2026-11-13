"""Authentication API."""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import bearer_scheme, get_current_user
from app.core.errors import conflict
from app.core.rate_limit import rate_limit
from app.core.security import TokenError, decode_access_token
from app.db.database import get_db
from app.db.models import User
from app.schemas.user import (
    ChangePasswordRequest,
    EmailOnlyRequest,
    GoogleAuthRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    OTPSentResponse,
    OTPVerifyRequest,
    ProfileUpdate,
    RefreshRequest,
    RegisterRequest,
    ResendOTPRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

_signup_limit = rate_limit("auth:register", 10, 3600)
_otp_send_limit = rate_limit("auth:otp-send", 10, 600)
_otp_verify_limit = rate_limit("auth:otp-verify", 30, 600)
_login_limit = rate_limit("auth:login", 20, 600)
_refresh_limit = rate_limit("auth:refresh", 60, 600)
# Google sign-in is a button people click repeatedly; per-email OTP caps still apply.
_google_limit = rate_limit("auth:google", 30, 600)


@router.post("/register", response_model=OTPSentResponse, status_code=202,
             dependencies=[Depends(_signup_limit)])
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Start signup. Creates a *pending* registration and emails a 6-digit code. No account exists yet."""
    return auth_service.start_registration(db, data, request)


@router.post("/verify-registration", response_model=TokenResponse, dependencies=[Depends(_otp_verify_limit)])
def verify_registration(data: OTPVerifyRequest, request: Request, db: Session = Depends(get_db)):
    """Verify the signup code; only now is the (customer) account created and signed in."""
    return auth_service.complete_registration(db, data.email, data.otp, request)


@router.post("/resend-otp", response_model=OTPSentResponse, dependencies=[Depends(_otp_send_limit)])
def resend_otp(data: ResendOTPRequest, request: Request, db: Session = Depends(get_db)):
    return auth_service.resend_otp(db, data.email, data.purpose, request)


@router.post("/verify-email", response_model=TokenResponse, dependencies=[Depends(_otp_verify_limit)])
def verify_email(data: OTPVerifyRequest, request: Request, db: Session = Depends(get_db)):
    """For accounts created before email verification existed (purpose=verify_email)."""
    return auth_service.verify_email(db, data.email, data.otp, request)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(_login_limit)])
@router.post("/login-password", response_model=TokenResponse, dependencies=[Depends(_login_limit)],
             include_in_schema=False)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return auth_service.login_with_password(db, data.email, data.password, request, data.location)


@router.post("/request-otp", response_model=OTPSentResponse, dependencies=[Depends(_otp_send_limit)])
def request_login_otp(data: EmailOnlyRequest, request: Request, db: Session = Depends(get_db)):
    """Passwordless sign-in for existing, verified accounts. Never creates an account."""
    return auth_service.request_login_otp(db, data.email, request)


@router.post("/verify-otp", response_model=TokenResponse, dependencies=[Depends(_otp_verify_limit)])
def verify_login_otp(data: OTPVerifyRequest, request: Request, db: Session = Depends(get_db)):
    return auth_service.login_with_otp(db, data.email, data.otp, request, "otp", data.location)


@router.post("/google", dependencies=[Depends(_google_limit)])
def google_login(data: GoogleAuthRequest, request: Request, db: Session = Depends(get_db)):
    """Verify the Google access token with Google, then email an OTP to the account address."""
    return auth_service.start_google_login(db, data.access_token, request)


@router.post("/google-verify-otp", response_model=TokenResponse, dependencies=[Depends(_otp_verify_limit)])
def google_verify_otp(data: OTPVerifyRequest, request: Request, db: Session = Depends(get_db)):
    return auth_service.login_with_otp(db, data.email, data.otp, request, "google", data.location)


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(_refresh_limit)])
def refresh(data: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    """Rotate the refresh token. A reused (already rotated) token revokes the whole session family."""
    return auth_service.refresh_session(db, data.refresh_token, request)


@router.post("/logout", response_model=MessageResponse)
def logout(data: Optional[LogoutRequest] = None,
           credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
           db: Session = Depends(get_db)):
    """
    Idempotent: always 200. Revokes the access token if it is still valid and the
    refresh-token family if one is given; an already expired/revoked session is
    simply "already signed out" rather than an error.
    """
    claims = None
    if credentials and credentials.credentials:
        try:
            claims = decode_access_token(credentials.credentials)
        except TokenError:
            claims = None
    auth_service.logout_any(db, claims, data.refresh_token if data else None)
    return {"message": "Signed out"}


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service.revoke_all_sessions(db, user)
    db.commit()
    return {"message": "Signed out of all devices"}


@router.post("/forgot-password", response_model=OTPSentResponse, dependencies=[Depends(_otp_send_limit)])
def forgot_password(data: EmailOnlyRequest, request: Request, db: Session = Depends(get_db)):
    return auth_service.request_password_reset(db, data.email, request)


@router.post("/reset-password", response_model=MessageResponse, dependencies=[Depends(_otp_verify_limit)])
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password(db, data.email, data.otp, data.new_password)
    return {"message": "Password reset. You can now sign in with your new password."}


@router.post("/change-password", response_model=TokenResponse)
def change_password(data: ChangePasswordRequest, request: Request, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return auth_service.change_password(db, user, data.current_password, data.new_password, request)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return auth_service.user_payload(user)


@router.patch("/me", response_model=UserResponse)
@router.patch("/update-profile", response_model=UserResponse, include_in_schema=False)
def update_profile(data: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update your own profile. Email, role and verification state cannot be changed here."""
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if field in ("full_name", "phone") and value is None:
            continue  # required fields cannot be cleared
        setattr(user, field, value if value != "" else None)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict("This mobile number is already registered to another account.", "PHONE_TAKEN")
    db.refresh(user)
    return auth_service.user_payload(user)
