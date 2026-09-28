import types

import pytest
import requests

from app.services import email_service as email_module
from app.services.email_service import EmailService


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(email_module.time, "sleep", lambda s: None)
    svc = EmailService()
    svc.api_key = "test-key"
    return svc


def response(status, body=None):
    return types.SimpleNamespace(status_code=status, text=str(body), json=lambda: body or {"messageId": "m1"})


def install_post(svc, outcomes):
    calls = []

    def post(url, headers=None, json=None, timeout=None):
        calls.append({"timeout": timeout, "to": json["to"][0]["email"]})
        outcome = outcomes[min(len(calls), len(outcomes)) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    svc.session = types.SimpleNamespace(post=post)
    return calls


def test_otp_success_first_try(service):
    calls = install_post(service, [response(201)])
    service._dispatch_api("a@x.com", "s", "<p/>", priority=True)
    assert len(calls) == 1
    # Regression: the OTP timeout used to be 1s and dropped emails during TLS setup
    connect, read = calls[0]["timeout"]
    assert connect >= 5 and read >= 10


def test_otp_retries_after_timeout(service):
    calls = install_post(service, [requests.exceptions.Timeout(), response(201)])
    service._dispatch_api("a@x.com", "s", "<p/>", priority=True)
    assert len(calls) == 2


def test_otp_retries_on_5xx_and_429(service):
    calls = install_post(service, [response(503), response(429), response(201)])
    service._dispatch_api("a@x.com", "s", "<p/>", priority=True)
    assert len(calls) == 3


def test_otp_gives_up_after_three_attempts(service):
    calls = install_post(service, [requests.exceptions.ConnectionError()])
    service._dispatch_api("a@x.com", "s", "<p/>", priority=True)
    assert len(calls) == 3


def test_4xx_is_not_retried(service):
    calls = install_post(service, [response(401, {"message": "bad key"})])
    service._dispatch_api("a@x.com", "s", "<p/>", priority=True)
    assert len(calls) == 1


def test_non_priority_mail_is_sent_once(service):
    calls = install_post(service, [requests.exceptions.Timeout()])
    service._dispatch_api("a@x.com", "s", "<p/>")
    assert len(calls) == 1


def test_missing_api_key_mocks_instead_of_sending():
    svc = EmailService()
    svc.api_key = None
    calls = install_post(svc, [response(201)])
    svc._dispatch_api("a@x.com", "s", "<p/>", priority=True)
    assert calls == []


def test_otp_email_contains_code(sent_emails):
    from app.services.email_service import email_service

    email_service.send_otp("a@x.com", "482913")
    assert sent_emails[0]["to"] == "a@x.com"
    assert "482913" in sent_emails[0]["subject"]
    assert "482913" in sent_emails[0]["html"]


def test_agent_resolution_mails_user_and_admin(sent_emails):
    from app.services.email_service import email_service

    email_service.send_agent_resolution(
        user_email="u@x.com", user_name="U", ticket_id="QX-1",
        complaint_subject="Refund", agent_solution="Refund issued", agent_name="QuickFix AI",
    )
    recipients = [e["to"] for e in sent_emails]
    assert recipients[0] == "u@x.com"
    assert email_service.admin_email in recipients
    assert "Refund issued" in sent_emails[0]["html"]
