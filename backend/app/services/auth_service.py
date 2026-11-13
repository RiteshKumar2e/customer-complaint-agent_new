"""
Account lifecycle: registration with email OTP, login, sessions and passwords.

Accounts are only ever created in `users` *after* the email OTP is verified;
until then the signup lives in `pending_registrations` and cannot log in or
call any protected API. Public registration can only create `customer`
accounts — roles are changed exclusively by admins or the server CLI.
"""
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Optional

import requests
from fastapi import Request
from sqlalchemy import or_, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, bad_request, conflict, forbidden, not_found, too_many, unauthorized, unavailable
from app.core.logging import get_logger, log_event
from app.core.security import (
    burn_password_check,
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.db.database import get_ist_time
from app.db.models import (
    OTP_LOGIN,
    OTP_PASSWORD_RESET,
    OTP_REGISTRATION,
    OTP_VERIFY_EMAIL,
    ROLE_CUSTOMER,
    LoginHistory,
    PendingRegistration,
    RefreshToken,
    RevokedAccessToken,
    User,
)
from app.schemas.user import UserResponse
from app.services import auth_emails, otp_service

logger = get_logger("app.auth")

PENDING_REGISTRATION_TTL = timedelta(hours=24)
GENERIC_LOGIN_ERROR = "Invalid email or password."


def client_ip(request: Optional[Request]) -> Optional[str]:
    return request.client.host if request is not None and request.client else None


def user_payload(user: User) -> dict:
    data = UserResponse.model_validate(user).model_dump()
    data["phone_required"] = not user.phone
    return data


def otp_sent(email: str, message: str) -> dict:
    s = get_settings()
    return {"message": message, "email": email, "expires_in": s.otp_ttl_seconds,
            "resend_after": s.otp_resend_cooldown_seconds, "requires_otp": True}


# ---------------------------------------------------------------------------
# Login history
# ---------------------------------------------------------------------------

def record_login(db: Session, user: User, method: str, request: Optional[Request], success: bool = True,
                 failure_reason: Optional[str] = None, location: Optional[str] = None) -> None:
    ua = (request.headers.get("user-agent") if request is not None else "") or ""
    lowered = ua.lower()
    device = "Mobile" if any(k in lowered for k in ("mobile", "iphone", "android")) else \
        "Tablet" if any(k in lowered for k in ("tablet", "ipad")) else "Desktop"
    db.add(LoginHistory(
        user_id=user.id, user_name=user.full_name, email=user.email, phone=user.phone, login_method=method,
        success=success, failure_reason=failure_reason, ip_address=client_ip(request), user_agent=ua[:500],
        device_type=device, status="Completed" if success else "Failed",
        login_location=(location or None) and location[:255],
    ))


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

def issue_tokens(db: Session, user: User, request: Optional[Request], family_id: Optional[str] = None) -> dict:
    s = get_settings()
    access, _claims = create_access_token(user.id, user.role, user.token_version)
    refresh = new_refresh_token()
    now = get_ist_time()
    db.add(RefreshToken(
        user_id=user.id, token_hash=hash_refresh_token(refresh), family_id=family_id or secrets.token_hex(16),
        created_at=now, expires_at=now + timedelta(days=s.refresh_token_days),
        user_agent=((request.headers.get("user-agent") if request is not None else "") or "")[:255],
        ip_address=client_ip(request),
    ))
    db.commit()
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer",
            "expires_in": s.access_token_minutes * 60, "user": user_payload(user)}


def refresh_session(db: Session, refresh_token: str, request: Optional[Request]) -> dict:
    now = get_ist_time()
    row = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token))
    ).scalar_one_or_none()
    if row is None:
        raise unauthorized("Session expired. Please sign in again.", "INVALID_REFRESH_TOKEN")
    if row.revoked_at is not None:
        # A rotated-out token was presented again: it was stolen or replayed.
        # Revoke every token in the family so neither party keeps the session.
        db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id,
                                              RefreshToken.revoked_at.is_(None)).values(revoked_at=now))
        db.commit()
        log_event(logger, 30, "refresh token reuse detected", user_id=row.user_id)
        raise unauthorized("Session expired. Please sign in again.", "REFRESH_TOKEN_REUSED")
    if now > row.expires_at:
        raise unauthorized("Session expired. Please sign in again.", "REFRESH_TOKEN_EXPIRED")
    user = db.get(User, row.user_id)
    if user is None or not user.is_active or not user.email_verified:
        raise unauthorized("Session expired. Please sign in again.", "INVALID_REFRESH_TOKEN")

    claimed = db.execute(
        update(RefreshToken).where(RefreshToken.id == row.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now).execution_options(synchronize_session=False)
    )
    if claimed.rowcount != 1:
        db.rollback()
        raise unauthorized("Session expired. Please sign in again.", "REFRESH_TOKEN_REUSED")
    tokens = issue_tokens(db, user, request, family_id=row.family_id)
    new_row = db.execute(select(RefreshToken).where(
        RefreshToken.token_hash == hash_refresh_token(tokens["refresh_token"]))).scalar_one()
    row.replaced_by_id = new_row.id
    db.commit()
    return tokens


def revoke_access_token(db: Session, jti: str, expires_at_epoch: int) -> None:
    from datetime import datetime, timezone

    from app.db.database import IST

    expires = datetime.fromtimestamp(expires_at_epoch, tz=timezone.utc).astimezone(IST).replace(tzinfo=None)
    if db.get(RevokedAccessToken, jti) is None:
        db.add(RevokedAccessToken(jti=jti, expires_at=expires))
    # Opportunistic cleanup of entries whose tokens have expired anyway.
    db.query(RevokedAccessToken).filter(RevokedAccessToken.expires_at < get_ist_time()).delete(
        synchronize_session=False)


def logout_any(db: Session, claims, refresh_token: Optional[str]) -> None:
    """Revoke whatever the client still holds; never fails for an already-ended session."""
    now = get_ist_time()
    user = db.get(User, claims.user_id) if claims is not None else None
    if claims is not None:
        revoke_access_token(db, claims.jti, claims.expires_at)
    if refresh_token:
        row = db.execute(select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token))).scalar_one_or_none()
        if row is not None and (user is None or row.user_id == user.id):
            db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id,
                                                  RefreshToken.revoked_at.is_(None)).values(revoked_at=now))
            user = user or db.get(User, row.user_id)
    if user is not None:
        last = db.execute(
            select(LoginHistory).where(LoginHistory.user_id == user.id, LoginHistory.success.is_(True),
                                       LoginHistory.logout_time.is_(None))
            .order_by(LoginHistory.login_time.desc()).limit(1)
        ).scalar_one_or_none()
        if last is not None:
            last.logout_time = now
    db.commit()


def logout(db: Session, user: User, jti: str, expires_at: int, refresh_token: Optional[str]) -> None:
    now = get_ist_time()
    revoke_access_token(db, jti, expires_at)
    if refresh_token:
        row = db.execute(select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token), RefreshToken.user_id == user.id)
        ).scalar_one_or_none()
        if row is not None:
            db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id,
                                                  RefreshToken.revoked_at.is_(None)).values(revoked_at=now))
    last = db.execute(
        select(LoginHistory).where(LoginHistory.user_id == user.id, LoginHistory.success.is_(True),
                                   LoginHistory.logout_time.is_(None))
        .order_by(LoginHistory.login_time.desc()).limit(1)
    ).scalar_one_or_none()
    if last is not None:
        last.logout_time = now
    db.commit()


def revoke_all_sessions(db: Session, user: User) -> None:
    """Invalidate every access and refresh token the user holds."""
    user.token_version = (user.token_version or 0) + 1
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
               .values(revoked_at=get_ist_time()))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def _assert_unique(db: Session, email: str, phone: str) -> None:
    """One round trip: which of email / phone is already taken."""
    taken = db.execute(
        select(User.email, User.phone).where(or_(User.email == email, User.phone == phone)).limit(2)
    ).all()
    if any(row.email == email for row in taken):
        raise conflict("An account with this email already exists. Please sign in instead.", "EMAIL_TAKEN")
    if taken:
        raise conflict("This mobile number is already registered to another account.", "PHONE_TAKEN")


def start_registration(db: Session, data, request: Optional[Request]) -> dict:
    # One round trip: email/phone uniqueness + OTP rate limits together.
    email_taken, phone_taken, *limits = db.execute(select(
        select(User.id).where(User.email == data.email).limit(1).scalar_subquery(),
        select(User.id).where(User.phone == data.phone).limit(1).scalar_subquery(),
        *otp_service.limit_columns(data.email, OTP_REGISTRATION),
    )).one()
    if email_taken is not None:
        raise conflict("An account with this email already exists. Please sign in instead.", "EMAIL_TAKEN")
    if phone_taken is not None:
        raise conflict("This mobile number is already registered to another account.", "PHONE_TAKEN")
    otp_service.enforce_limits(*limits)

    now = get_ist_time()
    values = dict(email=data.email, full_name=data.full_name, phone=data.phone, organization=data.organization,
                  password_hash=hash_password(data.password), created_at=now,
                  expires_at=now + PENDING_REGISTRATION_TTL)
    upsert = sqlite_insert(PendingRegistration).values(**values)
    db.execute(upsert.on_conflict_do_update(index_elements=[PendingRegistration.email],
                                            set_={k: v for k, v in values.items() if k != "email"}))
    # Committed together with the OTP row inside issue(); the email is already on its way by then.
    otp_service.issue(db, data.email, OTP_REGISTRATION, name=data.full_name, ip_address=client_ip(request),
                      check_limits=False)
    return otp_sent(data.email, "We sent a 6-digit verification code to your email. Enter it to activate your account.")


def _user_with_limits(db: Session, email: str, purpose: str):
    """One round trip: the account (if any) plus OTP rate-limit data for it."""
    row = db.execute(select(User, *otp_service.limit_columns(email, purpose)).where(User.email == email)).first()
    if row is None:
        return None, None
    return row[0], tuple(row[1:])


def complete_registration(db: Session, email: str, code: str, request: Optional[Request]) -> dict:
    pending = db.execute(select(PendingRegistration).where(PendingRegistration.email == email)).scalar_one_or_none()
    if pending is None:
        existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing is not None and existing.email_verified:
            raise conflict("This email is already verified. Please sign in.", "ALREADY_VERIFIED")
        raise bad_request("No pending registration for this email. Please sign up again.", "REGISTRATION_NOT_FOUND")
    if get_ist_time() > pending.expires_at:
        db.delete(pending)
        db.commit()
        raise bad_request("This registration has expired. Please sign up again.", "REGISTRATION_EXPIRED")

    otp_service.verify(db, email, OTP_REGISTRATION, code)
    try:
        _assert_unique(db, pending.email, pending.phone)
    except AppError:
        db.rollback()
        raise

    now = get_ist_time()
    user = User(
        email=pending.email, full_name=pending.full_name, phone=pending.phone, organization=pending.organization,
        hashed_password=pending.password_hash, is_active=True, role=ROLE_CUSTOMER,
        email_verified=True, email_verified_at=now, location="India", last_login_at=now,
    )
    db.add(user)
    db.delete(pending)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise conflict("An account with this email or mobile number already exists.", "ACCOUNT_EXISTS")
    record_login(db, user, "registration", request)
    db.commit()
    log_event(logger, 20, "account created", user_id=user.id)
    return issue_tokens(db, user, request)


def resend_otp(db: Session, email: str, purpose: str, request: Optional[Request]) -> dict:
    generic = otp_sent(email, "If this email can receive a code, a new one has been sent.")
    ip = client_ip(request)
    if purpose == OTP_REGISTRATION:
        pending = db.execute(select(PendingRegistration).where(PendingRegistration.email == email)).scalar_one_or_none()
        if pending is None or get_ist_time() > pending.expires_at:
            raise bad_request("No pending registration for this email. Please sign up again.", "REGISTRATION_NOT_FOUND")
        otp_service.issue(db, email, purpose, name=pending.full_name, ip_address=ip)
        return otp_sent(email, "A new verification code has been sent.")

    user, limits = _user_with_limits(db, email, purpose)
    if purpose == OTP_VERIFY_EMAIL:
        if user is None or user.email_verified or not user.is_active:
            return generic
    elif user is None or not user.is_active or (purpose == OTP_LOGIN and not user.email_verified):
        return generic
    otp_service.enforce_limits(*limits)
    otp_service.issue(db, email, purpose, name=user.full_name or "", ip_address=ip, check_limits=False)
    return generic


def verify_email(db: Session, email: str, code: str, request: Optional[Request]) -> dict:
    """Existing (pre-OTP) accounts confirm their address, then are signed in."""
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        raise bad_request("Incorrect or expired code.", "OTP_INVALID")
    if user.email_verified:
        raise conflict("This email is already verified. Please sign in.", "ALREADY_VERIFIED")
    otp_service.verify(db, email, OTP_VERIFY_EMAIL, code)
    if not user.is_active:
        db.rollback()
        raise forbidden("This account has been disabled.", "ACCOUNT_DISABLED")
    user.email_verified = True
    user.email_verified_at = get_ist_time()
    user.last_login_at = get_ist_time()
    record_login(db, user, "email_verification", request)
    db.commit()
    return issue_tokens(db, user, request)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login_with_password(db: Session, email: str, password: str, request: Optional[Request],
                        location: Optional[str] = None) -> dict:
    s = get_settings()
    now = get_ist_time()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        burn_password_check(password)
        raise unauthorized(GENERIC_LOGIN_ERROR, "INVALID_CREDENTIALS")

    if user.locked_until is not None and user.locked_until > now:
        minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise too_many(f"Too many failed sign-in attempts. Try again in {minutes} minute(s) or reset your password.",
                       retry_after=minutes * 60, code="ACCOUNT_LOCKED")

    matches, needs_rehash = verify_password(password, user.hashed_password)
    if not matches:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= s.login_max_failed:
            user.locked_until = now + timedelta(minutes=s.login_lockout_minutes)
            user.failed_login_attempts = 0
        record_login(db, user, "password", request, success=False, failure_reason="Invalid credentials",
                     location=location)
        db.commit()
        raise unauthorized(GENERIC_LOGIN_ERROR, "INVALID_CREDENTIALS")

    if not user.is_active:
        raise forbidden("This account has been disabled. Please contact support.", "ACCOUNT_DISABLED")
    if not user.email_verified:
        user.failed_login_attempts = 0
        db.commit()
        raise AppError(403, "Please verify your email address before signing in. We can send you a code.",
                       "EMAIL_NOT_VERIFIED")

    if needs_rehash:
        user.hashed_password = hash_password(password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    record_login(db, user, "password", request, location=location)
    db.commit()
    return issue_tokens(db, user, request)


def request_login_otp(db: Session, email: str, request: Optional[Request]) -> dict:
    return resend_otp(db, email, OTP_LOGIN, request)


def login_with_otp(db: Session, email: str, code: str, request: Optional[Request], method: str = "otp",
                   location: Optional[str] = None, google_sub: Optional[str] = None) -> dict:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not user.is_active or not user.email_verified:
        raise bad_request("Incorrect or expired code.", "OTP_INVALID")
    otp_service.verify(db, email, OTP_LOGIN, code)
    if google_sub and not user.google_id:
        clash = db.execute(select(User.id).where(User.google_id == google_sub)).first()
        if clash is None:
            user.google_id = google_sub
    user.last_login_at = get_ist_time()
    user.failed_login_attempts = 0
    user.locked_until = None
    record_login(db, user, method, request, location=location)
    db.commit()
    return issue_tokens(db, user, request)


# ---------------------------------------------------------------------------
# Google
# ---------------------------------------------------------------------------

def verify_google_access_token(access_token: str) -> dict:
    """Validate a Google OAuth access token server-side; return {email, sub, name}."""
    s = get_settings()
    if not s.google_client_id:
        raise unavailable("Google sign-in is not configured on this server.", "GOOGLE_NOT_CONFIGURED")
    try:
        info = requests.get("https://oauth2.googleapis.com/tokeninfo", params={"access_token": access_token},
                            timeout=8)
    except requests.RequestException:
        raise unavailable("Could not reach Google to verify sign-in. Please try again.", "GOOGLE_UNAVAILABLE")
    if info.status_code != 200:
        raise unauthorized("Google sign-in could not be verified.", "GOOGLE_TOKEN_INVALID")
    data = info.json()
    audience = data.get("aud") or data.get("azp")
    if audience != s.google_client_id and data.get("azp") != s.google_client_id:
        raise unauthorized("Google sign-in was issued for a different application.", "GOOGLE_TOKEN_INVALID")
    if str(data.get("email_verified")).lower() != "true" or not data.get("email"):
        raise unauthorized("Your Google account email is not verified.", "GOOGLE_EMAIL_UNVERIFIED")
    return {"email": data["email"].strip().lower(), "sub": data.get("sub")}


def start_google_login(db: Session, access_token: str, request: Optional[Request]) -> dict:
    identity = verify_google_access_token(access_token)
    email = identity["email"]
    user, limits = _user_with_limits(db, email, OTP_LOGIN)
    if user is None:
        raise not_found("No account uses this Google email yet. Please sign up first.", "ACCOUNT_NOT_FOUND")
    if not user.is_active:
        raise forbidden("This account has been disabled.", "ACCOUNT_DISABLED")
    # Even with Google's assertion, the account is unlocked only by an OTP sent to
    # the address on file — the same verification every other path requires.
    purpose = OTP_LOGIN if user.email_verified else OTP_VERIFY_EMAIL
    if purpose == OTP_LOGIN:
        otp_service.enforce_limits(*limits)
    otp_service.issue(db, email, purpose, name=user.full_name or "", ip_address=client_ip(request),
                      check_limits=purpose != OTP_LOGIN)
    result = otp_sent(email, "We sent a 6-digit code to your Google email address.")
    result["purpose"] = purpose
    return result


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------

def request_password_reset(db: Session, email: str, request: Optional[Request]) -> dict:
    user, limits = _user_with_limits(db, email, OTP_PASSWORD_RESET)
    message = "If an account exists for this email, we sent a 6-digit reset code."
    if user is not None and user.is_active:
        otp_service.enforce_limits(*limits)
        otp_service.issue(db, email, OTP_PASSWORD_RESET, name=user.full_name or "", ip_address=client_ip(request),
                          check_limits=False)
    return otp_sent(email, message)


def reset_password(db: Session, email: str, code: str, new_password: str) -> None:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise bad_request("Incorrect or expired code.", "OTP_INVALID")
    otp_service.verify(db, email, OTP_PASSWORD_RESET, code)
    user.hashed_password = hash_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    if not user.email_verified:
        # The reset code was delivered to and read from this inbox.
        user.email_verified = True
        user.email_verified_at = get_ist_time()
    revoke_all_sessions(db, user)
    db.commit()
    try:
        auth_emails.send_password_changed_notice(user.email, user.full_name or "")
    except Exception:
        logger.warning("Password-changed notice could not be sent")


def change_password(db: Session, user: User, current: str, new: str, request: Optional[Request]) -> dict:
    matches, _ = verify_password(current, user.hashed_password)
    if not matches:
        raise bad_request("Your current password is incorrect.", "INVALID_PASSWORD")
    if current == new:
        raise bad_request("Choose a password different from your current one.", "PASSWORD_UNCHANGED")
    user.hashed_password = hash_password(new)
    revoke_all_sessions(db, user)
    db.commit()
    try:
        auth_emails.send_password_changed_notice(user.email, user.full_name or "")
    except Exception:
        logger.warning("Password-changed notice could not be sent")
    return issue_tokens(db, user, request)
