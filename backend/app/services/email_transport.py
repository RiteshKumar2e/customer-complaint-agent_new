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


def _send_brevo(msg: EmailMessage, to: str, subject: str, html: str, text: str) -> None:
    s = get_settings()
    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": s.brevo_api_key, "Content-Type": "application/json", "Accept": "application/json"},
        json={
            "sender": {"name": s.smtp_from_name, "email": s.smtp_from_email},
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html,
            "textContent": text,
        },
        timeout=(5, 15),
    )
    if response.status_code not in (200, 201, 202):
        raise EmailDeliveryError(f"Brevo API returned HTTP {response.status_code}")


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
                _send_brevo(msg, to, subject, html, text)
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
