"""Input normalisation and validation shared by API schemas and migrations."""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

from email_validator import EmailNotValidError, validate_email

INDIAN_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

PASSWORD_MIN = 8
PASSWORD_MAX = 128


def validate_indian_mobile(value: Optional[str]) -> str:
    """
    Exactly 10 digits, first digit 6-9. No spaces, '+91', dashes or letters:
    the value must already be the bare 10-digit number.
    """
    if value is None or str(value) == "":
        raise ValueError("Mobile number is required")
    value = str(value)
    if not value.isascii() or not value.isdigit():
        raise ValueError("Mobile number must contain digits only (no spaces, letters or symbols)")
    if len(value) < 10:
        raise ValueError("Mobile number must be exactly 10 digits (too short)")
    if len(value) > 10:
        raise ValueError("Mobile number must be exactly 10 digits (too long)")
    if not INDIAN_MOBILE_RE.match(value):
        raise ValueError("Indian mobile numbers must start with 6, 7, 8 or 9")
    return value


def normalize_legacy_phone(raw: Optional[str]) -> Optional[str]:
    """
    Best-effort normalisation for phone numbers stored before validation existed
    (e.g. '+91 98765 43210'). Returns the 10-digit number or None if not valid.
    Used only by the data migration; new input must pass validate_indian_mobile.
    """
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if INDIAN_MOBILE_RE.match(digits) else None


def normalize_email(value: Optional[str]) -> str:
    if value is None or not str(value).strip():
        raise ValueError("Email is required")
    candidate = str(value).strip().lower()
    if len(candidate) > 100:
        raise ValueError("Email is too long")
    try:
        result = validate_email(candidate, check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValueError(f"Invalid email address: {exc}") from None
    return result.normalized.lower()


def validate_password(value: Optional[str]) -> str:
    if not value:
        raise ValueError("Password is required")
    if len(value) < PASSWORD_MIN:
        raise ValueError(f"Password must be at least {PASSWORD_MIN} characters")
    if len(value) > PASSWORD_MAX:
        raise ValueError(f"Password must be at most {PASSWORD_MAX} characters")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("Password must contain at least one letter and one number")
    return value


def clean_text(value: Optional[str], max_length: int, field: str = "Field", required: bool = False) -> Optional[str]:
    """Strip control characters and surrounding whitespace; enforce length."""
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return None
    text = unicodedata.normalize("NFC", str(value))
    text = _CONTROL_CHARS.sub("", text).strip()
    if required and not text:
        raise ValueError(f"{field} is required")
    if len(text) > max_length:
        raise ValueError(f"{field} must be at most {max_length} characters")
    return text


def validate_full_name(value: Optional[str]) -> str:
    name = clean_text(value, 100, "Full name", required=True)
    if len(name) < 2:
        raise ValueError("Full name must be at least 2 characters")
    if not re.search(r"[^\W\d_]", name):
        raise ValueError("Full name must contain letters")
    return name


def validate_otp_format(value: Optional[str]) -> str:
    code = (value or "").strip()
    if not re.fullmatch(r"\d{6}", code):
        raise ValueError("OTP must be exactly 6 digits")
    return code
