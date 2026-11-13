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


def test_brevo_uses_pooled_session_and_tags(monkeypatch):
    monkeypatch.setenv("EMAIL_TRANSPORT", "brevo")
    monkeypatch.setenv("BREVO_API_KEY", "key")
    monkeypatch.setenv("BREVO_SENDER_EMAIL", "support@example.com")
    from app.core.config import get_settings
    get_settings.cache_clear()
    calls = []

    class Resp:
        status_code = 201

    monkeypatch.setattr(email_transport._brevo, "post", lambda url, **kw: calls.append((url, kw)) or Resp())
    email_transport.send("to@x.com", "Code", "<p>123456</p>", "123456", category="otp:registration")
    url, kw = calls[0]
    assert url.endswith("/smtp/email") and kw["json"]["tags"] == ["otp"]
    assert kw["json"]["sender"]["email"] == "support@example.com" and kw["headers"]["api-key"] == "key"
    assert kw["timeout"][0] <= 3.05  # fail fast on connect


def test_brevo_rejection_raises(monkeypatch):
    monkeypatch.setenv("EMAIL_TRANSPORT", "brevo")
    monkeypatch.setenv("BREVO_API_KEY", "key")
    monkeypatch.setenv("BREVO_SENDER_EMAIL", "support@example.com")
    from app.core.config import get_settings
    get_settings.cache_clear()

    class Resp:
        status_code = 401

    monkeypatch.setattr(email_transport._brevo, "post", lambda url, **kw: Resp())
    with pytest.raises(email_transport.EmailDeliveryError):
        email_transport.send("to@x.com", "Code", "<p>x</p>", "x")


def test_warm_ping_sends_no_email(monkeypatch):
    monkeypatch.setenv("EMAIL_TRANSPORT", "brevo")
    monkeypatch.setenv("BREVO_API_KEY", "key")
    from app.core.config import get_settings
    get_settings.cache_clear()
    seen = []

    class Resp:
        status_code = 200

    monkeypatch.setattr(email_transport._brevo, "get", lambda url, **kw: seen.append(url) or Resp())
    monkeypatch.setattr(email_transport._brevo, "post", lambda *a, **k: pytest.fail("warm-up must not send email"))
    assert email_transport.warm_brevo_connection() is True
    assert seen == [f"{email_transport.BREVO_API}/account"]


def _brevo_env(monkeypatch, sender=""):
    monkeypatch.setenv("EMAIL_TRANSPORT", "brevo")
    monkeypatch.setenv("BREVO_API_KEY", "key-" + sender)
    monkeypatch.setenv("BREVO_SENDER_EMAIL", sender)
    monkeypatch.setenv("SMTP_FROM_EMAIL", "")
    monkeypatch.setenv("SENDER_EMAIL", "")
    from app.core.config import get_settings
    get_settings.cache_clear()
    email_transport._sender_cache.clear()


def test_brevo_sender_auto_detected_once(monkeypatch):
    _brevo_env(monkeypatch)
    gets, posts = [], []

    class Senders:
        status_code = 200

        @staticmethod
        def json():
            return {"senders": [{"email": "old@x.com", "active": False}, {"email": "ok@x.com", "active": True}]}

    class Sent:
        status_code = 201

    monkeypatch.setattr(email_transport._brevo, "get", lambda url, **kw: gets.append(url) or Senders())
    monkeypatch.setattr(email_transport._brevo, "post", lambda url, **kw: posts.append(kw["json"]) or Sent())
    email_transport.send("a@x.com", "s", "<p>h</p>", "h")
    email_transport.send("b@x.com", "s", "<p>h</p>", "h")
    assert [p["sender"]["email"] for p in posts] == ["ok@x.com", "ok@x.com"]
    assert gets == [f"{email_transport.BREVO_API}/senders"]  # cached after the first lookup


def test_no_active_brevo_sender_fails_clearly(monkeypatch):
    _brevo_env(monkeypatch)

    class Senders:
        status_code = 200

        @staticmethod
        def json():
            return {"senders": [{"email": "x@x.com", "active": False}]}

    monkeypatch.setattr(email_transport._brevo, "get", lambda url, **kw: Senders())
    monkeypatch.setattr(email_transport._brevo, "post", lambda *a, **k: pytest.fail("must not send"))
    with pytest.raises(email_transport.EmailDeliveryError):
        email_transport.send("a@x.com", "s", "<p>h</p>", "h")


def test_explicit_sender_skips_lookup(monkeypatch):
    _brevo_env(monkeypatch, sender="set@x.com")

    class Sent:
        status_code = 201

    monkeypatch.setattr(email_transport._brevo, "get", lambda *a, **k: pytest.fail("no lookup needed"))
    posts = []
    monkeypatch.setattr(email_transport._brevo, "post", lambda url, **kw: posts.append(kw["json"]) or Sent())
    email_transport.send("a@x.com", "s", "<p>h</p>", "h")
    assert posts[0]["sender"]["email"] == "set@x.com"


def test_brevo_error_reason_is_reported(monkeypatch):
    _brevo_env(monkeypatch, sender="set@x.com")

    class Rejected:
        status_code = 401
        text = ""

        @staticmethod
        def json():
            return {"code": "unauthorized", "message": "We have detected you are using an unrecognised IP address"}

    monkeypatch.setattr(email_transport._brevo, "post", lambda *a, **k: Rejected())
    with pytest.raises(email_transport.EmailDeliveryError) as err:
        email_transport.send("a@x.com", "s", "<p>h</p>", "h")
    assert "unrecognised IP address" in str(err.value) and "key-" not in str(err.value)
    monkeypatch.setattr(email_transport._brevo, "get", lambda *a, **k: Rejected())
    assert email_transport.email_health().startswith("error: brevo HTTP 401")


def test_ready_reports_email_status(client):
    body = client.get("/health/ready").json()
    assert body["database"] == "ok" and body["email"] in ("ok", "not_configured")
