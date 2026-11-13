"""
Password hashing, JWTs, OTP and refresh-token hashing.

* Passwords: Argon2id (argon2-cffi). Hashes created by the previous code
  (bcrypt over a SHA-256 pre-hash, or plain bcrypt) still verify and are
  transparently upgraded to Argon2id on the next successful login.
* OTPs and refresh tokens are stored only as HMAC-SHA256 digests keyed with a
  server secret, so a database leak does not reveal usable codes or tokens.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Optional, Tuple

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()  # Argon2id with argon2-cffi's recommended parameters


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, stored_hash: Optional[str]) -> Tuple[bool, bool]:
    """Return (matches, needs_rehash)."""
    if not stored_hash or not password:
        return False, False
    if stored_hash.startswith("$argon2"):
        try:
            _hasher.verify(stored_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False, False
        return True, _hasher.check_needs_rehash(stored_hash)
    if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
        encoded = stored_hash.encode()
        prehashed = hashlib.sha256(password.encode("utf-8")).hexdigest().encode()
        try:
            if bcrypt.checkpw(prehashed, encoded):
                return True, True
            # Oldest accounts hashed the raw password (bcrypt truncates at 72 bytes).
            if bcrypt.checkpw(password.encode("utf-8")[:72], encoded):
                return True, True
        except ValueError:
            return False, False
    return False, False


# A real hash to compare against when the account does not exist, so response
# time does not reveal which emails are registered.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


def burn_password_check(password: str) -> None:
    try:
        _hasher.verify(_DUMMY_HASH, password or "x")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# HMAC helpers (OTP codes, refresh tokens)
# ---------------------------------------------------------------------------

def _hmac_key(label: str) -> bytes:
    secret = get_settings().jwt_secret_key.encode()
    return hmac.new(secret, f"quickfix:{label}".encode(), hashlib.sha256).digest()


def generate_otp() -> str:
    """Cryptographically secure 6-digit code (leading zeros allowed)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(email: str, purpose: str, code: str) -> str:
    message = f"{purpose}:{email.lower()}:{code}".encode()
    return hmac.new(_hmac_key("otp"), message, hashlib.sha256).hexdigest()


def otp_matches(email: str, purpose: str, code: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(email, purpose, code), stored_hash)


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hmac.new(_hmac_key("refresh"), token.encode(), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Access tokens (JWT)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AccessClaims:
    user_id: int
    role: str
    token_version: int
    jti: str
    expires_at: int


class TokenError(Exception):
    def __init__(self, message: str, code: str = "INVALID_TOKEN"):
        super().__init__(message)
        self.code = code


def create_access_token(user_id: int, role: str, token_version: int) -> Tuple[str, AccessClaims]:
    settings = get_settings()
    now = int(time.time())
    claims = AccessClaims(
        user_id=user_id,
        role=role,
        token_version=token_version,
        jti=uuid.uuid4().hex,
        expires_at=now + settings.access_token_minutes * 60,
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "tv": token_version,
        "jti": claims.jti,
        "type": "access",
        "iat": now,
        "nbf": now,
        "exp": claims.expires_at,
        "iss": "quickfix-api",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, claims


def decode_access_token(token: str) -> AccessClaims:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer="quickfix-api",
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("Access token expired", "TOKEN_EXPIRED")
    except jwt.PyJWTError:
        raise TokenError("Invalid access token")
    if payload.get("type") != "access":
        raise TokenError("Invalid token type")
    try:
        return AccessClaims(
            user_id=int(payload["sub"]),
            role=str(payload.get("role", "")),
            token_version=int(payload.get("tv", 0)),
            jti=str(payload["jti"]),
            expires_at=int(payload["exp"]),
        )
    except (KeyError, TypeError, ValueError):
        raise TokenError("Malformed access token")
