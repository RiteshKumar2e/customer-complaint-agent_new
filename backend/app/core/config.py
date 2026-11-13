"""
Central configuration, read once from the environment.

Every secret comes from the environment. In production the app refuses to
start when a required secret is missing (see `validate_for_startup`), instead of
quietly running with a default JWT key or a disposable database.
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    value = (os.getenv(name) or default).strip()
    # Hosting dashboards (Render's "add from .env") can keep an inline comment as
    # part of the value, e.g. "https://a.com   # required". Drop " #..." so a
    # pasted template cannot silently break CORS or other settings.
    if " #" in value or "\t#" in value:
        value = value.split(" #", 1)[0].split("\t#", 1)[0].strip()
    return value


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        raise RuntimeError(f"Environment variable {name} must be an integer, got {raw!r}")


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name).lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_list(name: str) -> List[str]:
    return [item.strip().rstrip("/") for item in _env(name).split(",") if item.strip()]


# Current public web app. Used only when neither FRONTEND_URL nor APP_URL is set,
# so the live site keeps working; set FRONTEND_URL to move to another domain.
DEFAULT_PUBLIC_URL = "https://riteshkr.online"


def _normalize_origins(values: List[str]) -> List[str]:
    """'riteshkr.online' or 'https://riteshkr.online/app/' -> 'https://riteshkr.online' (CORS matches origins exactly)."""
    from urllib.parse import urlsplit

    origins = []
    for value in values:
        candidate = value if "://" in value else f"https://{value}"
        parts = urlsplit(candidate)
        if parts.scheme in ("http", "https") and parts.netloc and "*" not in parts.netloc:
            origins.append(f"{parts.scheme}://{parts.netloc.lower()}")
    return list(dict.fromkeys(origins))


def _origins_from_app_url(app_url: str) -> List[str]:
    """CORS fallback when FRONTEND_URL is unset: APP_URL's origin plus its www/apex twin."""
    from urllib.parse import urlsplit

    parts = urlsplit(app_url) if app_url else None
    if not parts or not parts.scheme or not parts.netloc:
        return []
    host = parts.netloc
    twin = host[4:] if host.startswith("www.") else f"www.{host}"
    hosts = [host] if host.startswith(("localhost", "127.")) else [host, twin]
    return [f"{parts.scheme}://{h}" for h in hosts]


class ConfigError(RuntimeError):
    """Raised when the environment cannot support a safe startup."""


@dataclass(frozen=True)
class Settings:
    environment: str
    app_name: str
    company_name: str
    app_url: str

    # Database (Turso / libSQL only)
    turso_database_url: str
    turso_auth_token: str
    db_connect_timeout: float
    run_migrations_on_startup: bool

    # Auth
    jwt_secret_key: str
    jwt_secret_is_ephemeral: bool
    jwt_algorithm: str
    access_token_minutes: int
    refresh_token_days: int
    otp_ttl_seconds: int
    otp_resend_cooldown_seconds: int
    otp_max_per_hour: int
    otp_max_attempts: int
    otp_verify_window_minutes: int
    otp_max_failed_per_window: int
    login_max_failed: int
    login_lockout_minutes: int
    google_client_id: str

    # Email
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    smtp_use_ssl: bool
    smtp_starttls: bool
    smtp_timeout: float
    brevo_api_key: str
    email_transport: str
    admin_notification_email: str

    # HTTP
    frontend_urls: List[str]
    cors_origin_regex: Optional[str]
    max_request_bytes: int
    max_upload_bytes: int
    max_attachments_per_complaint: int

    # AI
    groq_api_key: str
    gemini_api_key: str
    ai_timeout_seconds: float
    auto_resolve_delay_seconds: int
    auto_resolve_min_confidence: float
    agent_can_view_unassigned: bool

    extra: dict = field(default_factory=dict)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"

    @property
    def email_configured(self) -> bool:
        if self.email_transport == "brevo":
            # The sender can be auto-detected from the Brevo account (see email_transport).
            return bool(self.brevo_api_key)
        if self.email_transport == "console":
            return not self.is_production
        return bool(self.smtp_host and self.smtp_port and self.smtp_from_email)

    @property
    def turso_is_remote(self) -> bool:
        return self.turso_database_url.split(":", 1)[0] in ("libsql", "https", "http", "wss", "ws")


def _detect_transport() -> str:
    explicit = _env("EMAIL_TRANSPORT").lower()
    if explicit:
        if explicit not in ("smtp", "brevo", "console"):
            raise ConfigError("EMAIL_TRANSPORT must be one of: smtp, brevo, console")
        return explicit
    # Brevo (HTTPS API) is the project's provider; it also works on hosts that block SMTP ports.
    if _env("BREVO_API_KEY"):
        return "brevo"
    if _env("SMTP_HOST"):
        return "smtp"
    return "console"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    environment = _env("ENVIRONMENT", "development").lower()
    if os.getenv("RENDER") and environment == "development":
        # Render sets RENDER=true on every service; treat it as production so a
        # forgotten ENVIRONMENT variable cannot downgrade the security checks.
        environment = "production"

    jwt_secret = _env("JWT_SECRET_KEY")
    ephemeral = False
    if not jwt_secret and environment != "production":
        # Development only: tokens stop working on restart, which is acceptable
        # locally and impossible in production (validate_for_startup refuses).
        jwt_secret = secrets.token_urlsafe(48)
        ephemeral = True

    from_email = _env("BREVO_SENDER_EMAIL") or _env("SMTP_FROM_EMAIL") or _env("SENDER_EMAIL")

    return Settings(
        environment=environment,
        app_name=_env("APP_NAME", "QuickFix Complaint Desk"),
        company_name=_env("COMPANY_NAME", "QuickFix"),
        app_url=_env("APP_URL", "http://localhost:5173").rstrip("/"),
        turso_database_url=_env("TURSO_DATABASE_URL"),
        turso_auth_token=_env("TURSO_AUTH_TOKEN"),
        db_connect_timeout=float(_env("DB_CONNECT_TIMEOUT", "10")),
        run_migrations_on_startup=_env_bool("RUN_MIGRATIONS_ON_STARTUP", True),
        jwt_secret_key=jwt_secret,
        jwt_secret_is_ephemeral=ephemeral,
        jwt_algorithm="HS256",
        access_token_minutes=_env_int("ACCESS_TOKEN_MINUTES", 15),
        refresh_token_days=_env_int("REFRESH_TOKEN_DAYS", 7),
        otp_ttl_seconds=_env_int("OTP_TTL_SECONDS", 300),
        otp_resend_cooldown_seconds=_env_int("OTP_RESEND_COOLDOWN_SECONDS", 60),
        otp_max_per_hour=_env_int("OTP_MAX_PER_HOUR", 5),
        otp_max_attempts=_env_int("OTP_MAX_ATTEMPTS", 5),
        otp_verify_window_minutes=_env_int("OTP_VERIFY_WINDOW_MINUTES", 15),
        otp_max_failed_per_window=_env_int("OTP_MAX_FAILED_PER_WINDOW", 10),
        login_max_failed=_env_int("LOGIN_MAX_FAILED", 5),
        login_lockout_minutes=_env_int("LOGIN_LOCKOUT_MINUTES", 15),
        google_client_id=_env("GOOGLE_CLIENT_ID"),
        smtp_host=_env("SMTP_HOST"),
        smtp_port=_env_int("SMTP_PORT", 587),
        smtp_username=_env("SMTP_USERNAME"),
        smtp_password=_env("SMTP_PASSWORD"),
        smtp_from_email=from_email,
        smtp_from_name=_env("BREVO_SENDER_NAME") or _env("SMTP_FROM_NAME", "Quickfix AI Support"),
        smtp_use_ssl=_env_bool("SMTP_USE_SSL", _env_int("SMTP_PORT", 587) == 465),
        smtp_starttls=_env_bool("SMTP_STARTTLS", _env_int("SMTP_PORT", 587) != 465),
        smtp_timeout=float(_env("SMTP_TIMEOUT", "15")),
        brevo_api_key=_env("BREVO_API_KEY"),
        email_transport=_detect_transport(),
        admin_notification_email=_env("ADMIN_NOTIFICATION_EMAIL") or _env("ADMIN_EMAIL"),
        frontend_urls=(_normalize_origins(_env_list("FRONTEND_URL"))
                       or _origins_from_app_url(_env("APP_URL"))
                       or (_origins_from_app_url(DEFAULT_PUBLIC_URL) if environment == "production" else [])),
        cors_origin_regex=_env("CORS_ORIGIN_REGEX") or None,
        max_request_bytes=_env_int("MAX_REQUEST_BYTES", 1_000_000),
        max_upload_bytes=_env_int("MAX_UPLOAD_BYTES", 2_000_000),
        max_attachments_per_complaint=_env_int("MAX_ATTACHMENTS_PER_COMPLAINT", 3),
        groq_api_key=_env("GROQ_API_KEY"),
        gemini_api_key=_env("GEMINI_API_KEY"),
        ai_timeout_seconds=float(_env("AI_TIMEOUT_SECONDS", "25")),
        auto_resolve_delay_seconds=_env_int("AUTO_RESOLVE_DELAY_SECONDS", 300),
        auto_resolve_min_confidence=float(_env("AUTO_RESOLVE_MIN_CONFIDENCE", "0.75")),
        agent_can_view_unassigned=_env_bool("AGENT_CAN_VIEW_UNASSIGNED", False),
    )


def validate_for_startup(settings: Optional[Settings] = None) -> List[str]:
    """
    Return a list of warnings for non-production, raise ConfigError for production.
    Called from app startup so a misconfigured deploy fails loudly.
    """
    s = settings or get_settings()
    problems: List[str] = []

    if not s.turso_database_url:
        problems.append("TURSO_DATABASE_URL is not set (Turso/libSQL is the only supported database).")
    elif s.turso_database_url.split(":", 1)[0] in ("postgres", "postgresql", "mysql", "sqlite"):
        problems.append("TURSO_DATABASE_URL must be a libsql:// (or https://) Turso URL.")

    if s.is_production:
        if not s.turso_is_remote:
            problems.append("Production requires a remote Turso database (libsql://...), not a local file.")
        if s.turso_is_remote and not (s.turso_auth_token or "authToken=" in s.turso_database_url):
            problems.append("TURSO_AUTH_TOKEN is not set.")
        if not _env("JWT_SECRET_KEY"):
            problems.append("JWT_SECRET_KEY is not set.")
        elif len(s.jwt_secret_key) < 32:
            problems.append("JWT_SECRET_KEY must be at least 32 characters.")
        if problems:
            # Only missing secrets / database are fatal: running without them is unsafe.
            raise ConfigError("Refusing to start in production:\n  - " + "\n  - ".join(problems))
        # Missing non-secret config degrades safely instead of taking the whole API
        # (and its health check) down: signup/OTP answer 503 until email works, and
        # CORS falls back to APP_URL.
        warnings: List[str] = []
        if not s.email_configured:
            missing = []
            if s.email_transport == "console":
                missing = ["BREVO_API_KEY", "BREVO_SENDER_EMAIL"]
            else:
                if s.email_transport == "brevo" and not s.brevo_api_key:
                    missing.append("BREVO_API_KEY")
                if s.email_transport == "smtp" and not s.smtp_host:
                    missing.append("SMTP_HOST")
                if not s.smtp_from_email:
                    missing.append("BREVO_SENDER_EMAIL (a sender address verified in Brevo)")
            warnings.append(
                "CRITICAL: email delivery is not configured (transport=" + s.email_transport + "; missing: "
                + ", ".join(missing) + "). Registration, OTP login and password reset return 503 until fixed."
            )
        elif s.email_transport == "brevo" and not s.smtp_from_email:
            warnings.append("BREVO_SENDER_EMAIL is not set; the first active verified sender in the Brevo "
                            "account will be used.")
        if not _env("FRONTEND_URL"):
            warnings.append(
                f"FRONTEND_URL is not set; CORS falls back to APP_URL-derived origins: {', '.join(s.frontend_urls) or 'none'}."
            )
        return warnings

    if problems and not s.is_test:
        raise ConfigError("Cannot start:\n  - " + "\n  - ".join(problems))
    warnings = list(problems)
    if s.jwt_secret_is_ephemeral:
        warnings.append("JWT_SECRET_KEY not set: using a random per-process key (development only).")
    if s.email_transport == "console":
        warnings.append("No SMTP configured: emails are written to EMAIL_OUTBOX_DIR as .eml files (development only).")
    return warnings
