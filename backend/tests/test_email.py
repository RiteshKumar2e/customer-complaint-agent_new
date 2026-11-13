"""Email transport and templates."""
import smtplib

import pytest

from app.services import auth_emails, email_transport
from app.services.email_service import EmailService, html_to_text


def test_otp_email_has_html_text_and_expiry_and_no_code_in_subject():
    subject, html_body, text_body = auth_emails.render_otp_email("042917", "registration", "Asha <b>")
    assert "042917" not in subject
    assert "042917" in html_body and "042917" in text_body
    assert "5 minutes" in html_body and "5 minutes" in text_body
    assert "&lt;b&gt;" in html_body  # name escaped
    assert "password" not in text_body.lower()


def test_smtp_transport_sends_multipart(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            sent["host"] = (host, port)

        def ehlo(self):
            pass

        def starttls(self, context=None):
            sent["tls"] = True

        def login(self, user, password):
            sent["login"] = user

        def send_message(self, msg):
            sent["msg"] = msg

        def quit(self):
            pass

    monkeypatch.setenv("EMAIL_TRANSPORT", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "mailer")
    monkeypatch.setenv("SMTP_PASSWORD", "pw")
    from app.core.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    email_transport.send("to@x.com", "Hello", "<p>Hi</p>", "Hi")
    assert sent["host"] == ("smtp.example.com", 587) and sent["tls"] and sent["login"] == "mailer"
    assert sent["msg"].is_multipart() and sent["msg"]["To"] == "to@x.com"


def test_smtp_failure_raises(monkeypatch):
    class Broken:
        def __init__(self, *a, **k):
            raise OSError("connection refused")

    monkeypatch.setenv("EMAIL_TRANSPORT", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    from app.core.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setattr(smtplib, "SMTP", Broken)
    monkeypatch.setattr(email_transport.time, "sleep", lambda s: None)
    with pytest.raises(email_transport.EmailDeliveryError):
        email_transport.send("to@x.com", "Hello", "<p>Hi</p>", "Hi", retries=1)


def test_console_transport_refused_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.core.config import get_settings
    get_settings.cache_clear()
    with pytest.raises(email_transport.EmailDeliveryError):
        email_transport._send_console(email_transport.build_message("a@x.com", "s", "<p>h</p>", "h"))


def test_notification_templates_escape_user_input(outbox, monkeypatch):
    import app.services.email_service as module

    class Inline:
        @staticmethod
        def submit(fn, *args):
            fn(*args)

    monkeypatch.setattr(module, "_executor", Inline)
    EmailService().send_complaint_confirmation("<script>x</script>", "c@x.com",
                                               {"ticket_id": "QX-1", "subject": "<img src=x>", "category": "Billing"})
    html = outbox.to("c@x.com")[0]["html"]
    assert "<script>x</script>" not in html and "<img src=x>" not in html
    assert outbox.to("ops@example.com")  # staff copy goes to ADMIN_NOTIFICATION_EMAIL


def test_public_send_escapes(outbox, monkeypatch):
    import app.services.email_service as module

    class Inline:
        @staticmethod
        def submit(fn, *args):
            fn(*args)

    monkeypatch.setattr(module, "_executor", Inline)
    EmailService().send_agent_resolution("c@x.com", "<b>Eve</b>", "QX-9", "<i>s</i>", "<img src=x onerror=1>",
                                         "Agent", ["<script>1</script>"])
    html = outbox.to("c@x.com")[0]["html"]
    assert "<img src=x" not in html and "<script>1</script>" not in html


def test_html_to_text():
    assert html_to_text("<p>Hello<br>World</p><style>x{}</style>") == "Hello\nWorld"
