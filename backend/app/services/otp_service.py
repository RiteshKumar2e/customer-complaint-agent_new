"""
Email one-time passwords.

Rules (all enforced from Turso data, so they hold across restarts/instances):
  * 6-digit code from `secrets`; only an HMAC-SHA256 digest is stored.
  * expires after OTP_TTL_SECONDS (default 300 s = 5 minutes); single use.
  * a new code invalidates any earlier unused code for the same email+purpose.
  * resend cooldown OTP_RESEND_COOLDOWN_SECONDS (60 s) per email+purpose.
  * at most OTP_MAX_PER_HOUR (5) codes per email per hour, across purposes.
  * at most OTP_MAX_ATTEMPTS (5) wrong guesses per code, and at most
    OTP_MAX_FAILED_PER_WINDOW (10) wrong guesses per email per
    OTP_VERIFY_WINDOW_MINUTES (15) across codes — brute force is not viable.
  * if the email cannot be delivered the code is discarded and the caller gets
    a 503; nothing is activated.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import bad_request, too_many, unavailable
from app.core.logging import get_logger, log_event
from app.core.security import generate_otp, hash_otp, otp_matches
from app.db.database import get_ist_time
from app.db.models import OTP_PURPOSES, EmailOTP
from app.services import auth_emails
from app.services.email_transport import EmailDeliveryError

logger = get_logger("app.otp")


def _latest(db: Session, email: str, purpose: str) -> Optional[EmailOTP]:
    return db.execute(
        select(EmailOTP)
        .where(EmailOTP.email == email, EmailOTP.purpose == purpose)
        .order_by(EmailOTP.created_at.desc(), EmailOTP.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def assert_can_issue(db: Session, email: str, purpose: str) -> None:
    """Raise 429 if a new code may not be sent yet (cooldown / hourly cap)."""
    s = get_settings()
    now = get_ist_time()
    last = _latest(db, email, purpose)
    if last is not None:
        elapsed = (now - last.created_at).total_seconds()
        if elapsed < s.otp_resend_cooldown_seconds:
            wait = int(s.otp_resend_cooldown_seconds - elapsed) + 1
            raise too_many(f"Please wait {wait} seconds before requesting a new code.", retry_after=wait,
                           code="OTP_COOLDOWN")

    window_start = now - timedelta(hours=1)
    issued = db.execute(
        select(func.count(EmailOTP.id)).where(EmailOTP.email == email, EmailOTP.created_at >= window_start)
    ).scalar_one()
    if issued >= s.otp_max_per_hour:
        oldest = db.execute(
            select(func.min(EmailOTP.created_at)).where(EmailOTP.email == email, EmailOTP.created_at >= window_start)
        ).scalar_one()
        wait = int(3600 - (now - oldest).total_seconds()) + 1 if oldest else 3600
        raise too_many("Too many verification codes were requested for this email. Please try again later.",
                       retry_after=wait, code="OTP_RATE_LIMITED")


def issue(db: Session, email: str, purpose: str, name: str = "", ip_address: Optional[str] = None) -> None:
    """Create, persist and email a new code. Commits. Raises 429/503 on failure."""
    if purpose not in OTP_PURPOSES:
        raise ValueError(f"unknown OTP purpose {purpose}")
    s = get_settings()
    assert_can_issue(db, email, purpose)
    now = get_ist_time()

    db.execute(
        update(EmailOTP)
        .where(EmailOTP.email == email, EmailOTP.purpose == purpose,
               EmailOTP.consumed_at.is_(None), EmailOTP.invalidated_at.is_(None))
        .values(invalidated_at=now)
    )
    code = generate_otp()
    record = EmailOTP(
        email=email, purpose=purpose, code_hash=hash_otp(email, purpose, code),
        created_at=now, expires_at=now + timedelta(seconds=s.otp_ttl_seconds), attempts=0,
        ip_address=(ip_address or "")[:64] or None,
    )
    db.add(record)
    db.commit()

    try:
        auth_emails.send_otp_email(email, code, purpose, name)
    except EmailDeliveryError:
        # The code never reached the user: discard it so it cannot be used and
        # does not count against their hourly allowance.
        db.delete(record)
        db.commit()
        log_event(logger, 40, "otp email failed", purpose=purpose)
        raise unavailable("We could not send the verification email right now. Please try again in a few minutes.",
                          code="EMAIL_DELIVERY_FAILED")
    log_event(logger, 20, "otp issued", purpose=purpose, otp_id=record.id)


def _recent_failures(db: Session, email: str) -> int:
    s = get_settings()
    since = get_ist_time() - timedelta(minutes=s.otp_verify_window_minutes)
    return int(db.execute(
        select(func.coalesce(func.sum(EmailOTP.attempts), 0)).where(EmailOTP.email == email,
                                                                   EmailOTP.created_at >= since)
    ).scalar_one())


def verify(db: Session, email: str, purpose: str, code: str) -> EmailOTP:
    """
    Check a code and mark it consumed (without committing — the caller commits
    the consumption together with whatever the code unlocks, atomically).
    """
    s = get_settings()
    now = get_ist_time()

    if _recent_failures(db, email) >= s.otp_max_failed_per_window:
        raise too_many(
            f"Too many incorrect codes. Please wait {s.otp_verify_window_minutes} minutes and request a new code.",
            retry_after=s.otp_verify_window_minutes * 60, code="OTP_LOCKED")

    record = _latest(db, email, purpose)
    if record is None:
        raise bad_request("No verification code is pending for this email. Please request a new code.",
                          "OTP_NOT_FOUND")

    if not otp_matches(email, purpose, code, record.code_hash):
        reused = db.execute(
            select(EmailOTP.id, EmailOTP.code_hash, EmailOTP.consumed_at)
            .where(EmailOTP.email == email, EmailOTP.purpose == purpose, EmailOTP.id != record.id,
                   EmailOTP.created_at >= now - timedelta(hours=1))
        ).all()
        record.attempts = (record.attempts or 0) + 1
        remaining = s.otp_max_attempts - record.attempts
        if remaining <= 0 and record.invalidated_at is None and record.consumed_at is None:
            record.invalidated_at = now
        db.commit()
        for _id, old_hash, consumed_at in reused:
            if otp_matches(email, purpose, code, old_hash):
                if consumed_at is not None:
                    raise bad_request("This code has already been used. Please request a new code.", "OTP_ALREADY_USED")
                raise bad_request("This code was replaced by a newer one. Use the latest code we emailed you.",
                                  "OTP_SUPERSEDED")
        if record.consumed_at is not None or record.invalidated_at is not None or now > record.expires_at:
            raise bad_request("Incorrect code. Please request a new code.", "OTP_INVALID")
        if remaining <= 0:
            raise bad_request("Too many incorrect attempts for this code. Please request a new code.",
                              "OTP_ATTEMPTS_EXCEEDED")
        raise bad_request(f"Incorrect code. {remaining} attempt{'s' if remaining != 1 else ''} left.", "OTP_INVALID")

    if record.consumed_at is not None:
        raise bad_request("This code has already been used. Please request a new code.", "OTP_ALREADY_USED")
    if record.invalidated_at is not None:
        if record.attempts >= s.otp_max_attempts:
            raise bad_request("Too many incorrect attempts for this code. Please request a new code.",
                              "OTP_ATTEMPTS_EXCEEDED")
        raise bad_request("This code is no longer valid. Please request a new code.", "OTP_INVALIDATED")
    if now > record.expires_at:
        raise bad_request("This code has expired. Please request a new code.", "OTP_EXPIRED")

    # Conditional update: only one concurrent request can consume the code.
    result = db.execute(
        update(EmailOTP)
        .where(EmailOTP.id == record.id, EmailOTP.consumed_at.is_(None), EmailOTP.invalidated_at.is_(None))
        .values(consumed_at=now)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        raise bad_request("This code has already been used. Please request a new code.", "OTP_ALREADY_USED")
    record.consumed_at = now
    return record
