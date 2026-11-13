"""Auth and profile schemas. Unknown fields are rejected (e.g. a `role` in a signup body)."""
from __future__ import annotations

import base64
import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validators import (
    clean_text,
    normalize_email,
    validate_full_name,
    validate_indian_mobile,
    validate_otp_format,
    validate_password,
)

MAX_PROFILE_IMAGE_BYTES = 300_000
_DATA_URL = re.compile(r"^data:image/(png|jpeg|jpg|webp|gif);base64,([A-Za-z0-9+/=\s]+)$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)


class EmailField(StrictModel):
    email: str

    @field_validator("email", mode="before")
    @classmethod
    def _email(cls, v):
        return normalize_email(v)


class RegisterRequest(EmailField):
    full_name: str
    phone: str
    password: str
    organization: Optional[str] = None

    @field_validator("full_name", mode="before")
    @classmethod
    def _name(cls, v):
        return validate_full_name(v)

    @field_validator("phone", mode="before")
    @classmethod
    def _phone(cls, v):
        return validate_indian_mobile(v if v is None else str(v))

    @field_validator("password", mode="before")
    @classmethod
    def _password(cls, v):
        return validate_password(v)

    @field_validator("organization", mode="before")
    @classmethod
    def _org(cls, v):
        return clean_text(v, 100, "Organization") or None


class OTPVerifyRequest(EmailField):
    otp: str
    location: Optional[str] = Field(default=None, max_length=255)

    @field_validator("otp", mode="before")
    @classmethod
    def _otp(cls, v):
        return validate_otp_format(v)


class ResendOTPRequest(EmailField):
    purpose: Literal["registration", "verify_email", "login", "password_reset"] = "registration"


class LoginRequest(EmailField):
    password: str = Field(min_length=1, max_length=128)
    location: Optional[str] = Field(default=None, max_length=255)


class EmailOnlyRequest(EmailField):
    pass


class ResetPasswordRequest(EmailField):
    otp: str
    new_password: str

    @field_validator("otp", mode="before")
    @classmethod
    def _otp(cls, v):
        return validate_otp_format(v)

    @field_validator("new_password", mode="before")
    @classmethod
    def _password(cls, v):
        return validate_password(v)


class ChangePasswordRequest(StrictModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str

    @field_validator("new_password", mode="before")
    @classmethod
    def _password(cls, v):
        return validate_password(v)


class RefreshRequest(StrictModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class LogoutRequest(StrictModel):
    refresh_token: Optional[str] = Field(default=None, max_length=200)


class GoogleAuthRequest(StrictModel):
    access_token: str = Field(min_length=10, max_length=4096)
    location: Optional[str] = Field(default=None, max_length=255)


class ProfileUpdate(StrictModel):
    """Self-service profile edits. Role, email and verification state are NOT editable here."""

    full_name: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None

    @field_validator("full_name", mode="before")
    @classmethod
    def _name(cls, v):
        return None if v is None else validate_full_name(v)

    @field_validator("phone", mode="before")
    @classmethod
    def _phone(cls, v):
        return None if v is None else validate_indian_mobile(str(v))

    @field_validator("organization", "job_title", "location", mode="before")
    @classmethod
    def _short(cls, v):
        return clean_text(v, 100, "Field")

    @field_validator("bio", mode="before")
    @classmethod
    def _bio(cls, v):
        return clean_text(v, 1000, "Bio")

    @field_validator("profile_image", mode="before")
    @classmethod
    def _image(cls, v):
        if v is None or v == "":
            return v
        match = _DATA_URL.match(str(v))
        if not match:
            raise ValueError("Profile image must be a PNG, JPEG, WEBP or GIF data URL")
        try:
            raw = base64.b64decode(match.group(2), validate=False)
        except Exception:
            raise ValueError("Profile image is not valid base64")
        if len(raw) > MAX_PROFILE_IMAGE_BYTES:
            raise ValueError("Profile image must be 300 KB or smaller")
        return str(v)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    role: str
    department: Optional[str] = None
    email_verified: bool
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    phone_required: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class OTPSentResponse(BaseModel):
    message: str
    email: str
    expires_in: int
    resend_after: int
    requires_otp: bool = True


class MessageResponse(BaseModel):
    message: str
