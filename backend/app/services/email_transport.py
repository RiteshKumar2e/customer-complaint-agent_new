"""
Email delivery transports.

* smtp    — default. Configure SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
            SMTP_FROM_EMAIL, SMTP_FROM_NAME. Port 465 uses implicit TLS, others STARTTLS.
* brevo   — Brevo's HTTPS API (BREVO_API_KEY). Useful on hosts that block
            outbound SMTP ports (e.g. some free PaaS tiers).
* console — development only: the message is written to EMAIL_OUTBOX_DIR as an
            .eml file (like a local mail catcher). Refused in production.

`send()` raises EmailDeliveryError on failure so callers that MUST know (OTP
delivery) can react. Logs record recipient domain, category and outcome only —
never message bodies, so OTP codes cannot leak into logs.
"""
from __future__ import annotations

import os
import smtplib
import ssl
import time
import uuid
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Optional

import requests

from app.core.config import get_settings
from app.core.logging import get_logger, log_event

logger = get_logger("app.email")


class EmailDeliveryError(Exception):
    pass


def _mask(address: str) -> str:
    local, _, domain = address.partition("@")
    return f"{local[:2]}***@{domain}" if domain else "***"


def build_message(to: str, subject: str, html: str, text: str) -> EmailMessage:
    s = get_settings()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((s.smtp_from_name, s.smtp_from_email or "no-reply@localhost"))
    msg["To"] = to
    msg["Message-ID"] = make_msgid(domain=(s.smtp_from_email.split("@")[-1] if s.smtp_from_email else None))
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


def _send_smtp(msg: EmailMessage) -> None:
    s = get_settings()
    context = ssl.create_default_context()
    if s.smtp_use_ssl:
        server = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, timeout=s.smtp_timeout, context=context)
    else:
        server = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=s.smtp_timeout)
    try:
        server.ehlo()
        if not s.smtp_use_ssl and s.smtp_starttls:
            server.starttls(context=context)
            server.ehlo()
        if s.smtp_username:
            server.login(s.smtp_username, s.smtp_password)
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass


BREVO_API = "https://api.brevo.com/v3"

# One pooled HTTPS session: reusing the TLS connection cuts each Brevo call from
# ~760 ms to ~310 ms (measured). keep_brevo_warm() stops it from going idle.
_brevo = requests.Session()
_brevo.mount("https://", requests.adapters.HTTPAdapter(pool_connections=2, pool_maxsize=10, max_retries=0))


def _brevo_headers() -> dict:
    return {"api-key": get_settings().brevo_api_key, "Content-Type": "application/json",
            "Accept": "application/json"}


_sender_cache: dict = {}


def brevo_sender() -> dict:
    """
    Sender for Brevo: BREVO_SENDER_EMAIL if set, otherwise the first *active,
    verified* sender on the Brevo account (looked up once and cached).
    """
    s = get_settings()
    if s.smtp_from_email:
        return {"name": s.smtp_from_name, "email": s.smtp_from_email}
    if s.brevo_api_key in _sender_cache:
        return _sender_cache[s.brevo_api_key]
    try:
        response = _brevo.get(f"{BREVO_API}/senders", headers=_brevo_headers(), timeout=(3.05, 8))
    except requests.RequestException as exc:
        raise EmailDeliveryError("Could not look up the Brevo sender") from exc
    if response.status_code != 200:
        raise EmailDeliveryError(f"Brevo sender lookup returned HTTP {response.status_code}")
    active = [x for x in response.json().get("senders", []) if x.get("active") and x.get("email")]
    if not active:
        raise EmailDeliveryError("The Brevo account has no active verified sender; set BREVO_SENDER_EMAIL")
    sender = {"name": s.smtp_from_name, "email": active[0]["email"]}
    _sender_cache[s.brevo_api_key] = sender
    log_event(logger, 20, "brevo sender auto-detected", sender=_mask(sender["email"]))
    return sender


def _send_brevo(msg: EmailMessage, to: str, subject: str, html: str, text: str, category: str = "") -> None:
    payload = {
        "sender": brevo_sender(),
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
        "textContent": text,
    }
    if category:
        payload["tags"] = [category.split(":")[0]]
    response = _brevo.post(f"{BREVO_API}/smtp/email", headers=_brevo_headers(), json=payload, timeout=(3.05, 10))
    if response.status_code not in (200, 201, 202):
        raise EmailDeliveryError(f"Brevo API returned HTTP {response.status_code}")


def warm_brevo_connection() -> bool:
    """Open (or keep open) the pooled TLS connection with a cheap authenticated GET. Sends nothing."""
    s = get_settings()
    if s.email_transport != "brevo" or not s.brevo_api_key:
        return False
    try:
        ok = _brevo.get(f"{BREVO_API}/account", headers=_brevo_headers(), timeout=(3.05, 5)).status_code == 200
        if ok and not s.smtp_from_email:
            brevo_sender()  # resolve once at startup instead of during the first OTP
        return ok
    except (requests.RequestException, EmailDeliveryError):
        return False


async def keep_brevo_warm(interval_seconds: int = 50) -> None:
    """Background task: keeps the connection alive so the first OTP after a quiet spell is fast too."""
    import asyncio

    while True:
        await asyncio.to_thread(warm_brevo_connection)
        await asyncio.sleep(interval_seconds)


def _send_console(msg: EmailMessage) -> None:
    s = get_settings()
    if s.is_production:
        raise EmailDeliveryError("Console email transport is disabled in production")
    outbox = os.getenv("EMAIL_OUTBOX_DIR", ".outbox")
    os.makedirs(outbox, exist_ok=True)
    path = os.path.join(outbox, f"{int(time.time())}-{uuid.uuid4().hex[:8]}.eml")
    with open(path, "wb") as handle:
        handle.write(bytes(msg))


def send(to: str, subject: str, html: str, text: str, category: str = "notification", retries: int = 0) -> None:
    """Deliver one message synchronously. Raises EmailDeliveryError."""
    s = get_settings()
    if not to or "@" not in to:
        raise EmailDeliveryError("Invalid recipient")
    msg = build_message(to, subject, html, text)
    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            if s.email_transport == "smtp":
                if not s.smtp_host:
                    raise EmailDeliveryError("SMTP is not configured")
                _send_smtp(msg)
            elif s.email_transport == "brevo":
                _send_brevo(msg, to, subject, html, text, category)
            else:
                _send_console(msg)
            log_event(logger, 20, "email delivered", category=category, to=_mask(to),
                      transport=s.email_transport, attempt=attempt + 1)
            return
        except (smtplib.SMTPException, OSError, requests.RequestException, EmailDeliveryError) as exc:
            last_error = exc
            log_event(logger, 30, "email delivery failed", category=category, to=_mask(to),
                      transport=s.email_transport, attempt=attempt + 1, error=type(exc).__name__)
            if isinstance(exc, smtplib.SMTPAuthenticationError):
                break  # bad credentials will not fix themselves
            if attempt < retries:
                time.sleep(min(2 ** attempt, 4))
    raise EmailDeliveryError("Email could not be delivered") from last_error
