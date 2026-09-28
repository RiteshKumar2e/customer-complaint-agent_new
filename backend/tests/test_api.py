"""End-to-end API tests through FastAPI's TestClient (LLMs and email stubbed)."""
import json

import pytest
from fastapi.testclient import TestClient

from app.db import models
from qf_testutils import scores

ADMIN = "riteshkumar90359@gmail.com"


@pytest.fixture
def client(monkeypatch, sent_emails):
    from app.main import app
    from app.api import routes

    async def pipeline(text, user_language="english"):
        return {
            "category": "Billing", "priority": "High", "response": "We are on it",
            "action": "Escalate to human support immediately", "sentiment": "Negative",
            "solution": "1. Refund within 3 days.", "satisfaction": "Medium",
            "similar_issues": "", "steps": [{"step": "Master Intelligence", "status": "Done"}],
        }

    monkeypatch.setattr(routes, "run_agent_pipeline", pipeline)
    # Background auto-resolution is covered in test_auto_resolver; keep API tests fast
    queued = []

    async def fake_process(complaint_id, delay=None):
        queued.append(complaint_id)

    monkeypatch.setattr(routes.auto_resolver, "process_complaint", fake_process)
    test_client = TestClient(app)
    test_client.queued = queued
    return test_client


def make_user(db, email, role="Strategic Member", is_agent=False):
    user = models.User(email=email, full_name=email.split("@")[0], role=role, is_agent=is_agent, is_active=True)
    db.add(user)
    db.commit()
    return user


# --- health / auth ----------------------------------------------------------------

def test_health(client):
    assert client.get("/health").status_code == 200


def test_otp_login_flow(client, db, sent_emails):
    res = client.post("/auth/request-otp", json={"email": "new@x.com"})
    assert res.status_code == 200

    otp_mail = next(e for e in sent_emails if e["to"] == "new@x.com")
    db.expire_all()
    otp = db.query(models.User).filter_by(email="new@x.com").one().otp
    assert otp in otp_mail["subject"]

    bad = client.post("/auth/verify-otp", json={"email": "new@x.com", "otp": "000000" if otp != "000000" else "111111"})
    assert bad.status_code == 400

    good = client.post("/auth/verify-otp", json={"email": "new@x.com", "otp": otp})
    assert good.status_code == 200
    assert good.json()["access_token"]

    reused = client.post("/auth/verify-otp", json={"email": "new@x.com", "otp": otp})
    assert reused.status_code == 400  # OTP is single-use


def test_google_otp_flow(client, db, sent_emails):
    assert client.post("/auth/google", json={"token": "g@x.com", "name": "G"}).status_code == 200
    db.expire_all()
    otp = db.query(models.User).filter_by(email="g@x.com").one().otp
    res = client.post("/auth/google-verify-otp", json={"email": "g@x.com", "otp": otp})
    assert res.status_code == 200 and res.json()["user"]["email"] == "g@x.com"


def test_register_and_password_login(client):
    body = {"email": "p@x.com", "full_name": "P", "phone": "1", "organization": "O", "password": "dummy-test-password"}
    assert client.post("/auth/register", json=body).status_code == 200
    assert client.post("/auth/register", json=body).status_code == 400  # duplicate

    ok = client.post("/auth/login-password", json={"email": "p@x.com", "password": "dummy-test-password"})
    assert ok.status_code == 200
    wrong = client.post("/auth/login-password", json={"email": "p@x.com", "password": "nope"})
    assert wrong.status_code == 401
    missing = client.post("/auth/login-password", json={"email": "ghost@x.com", "password": "x"})
    assert missing.status_code == 404


# --- complaints -----------------------------------------------------------------

def test_submit_complaint_saves_and_queues_auto_resolution(client, db):
    res = client.post("/complaint", json={
        "name": "Asha", "email": "asha@x.com", "subject": "Double charge", "description": "Charged twice",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["ticket_id"].startswith("QX-")
    assert body["category"] == "Billing"

    complaint = db.query(models.Complaint).filter_by(ticket_id=body["ticket_id"]).one()
    assert complaint.solution == "1. Refund within 3 days."
    assert json.loads(complaint.ai_analysis_steps)[0]["step"] == "Master Intelligence"
    assert client.queued == [complaint.id]


# --- agent module -----------------------------------------------------------------

@pytest.fixture
def ticket(db):
    complaint = models.Complaint(
        ticket_id="QX-AGENT-1", name="U", email="u@x.com", subject="Refund", description="No refund",
        complaint_text="No refund", category="Billing", priority="High", solution="draft", is_resolved=False,
    )
    db.add(complaint)
    db.commit()
    return complaint


def test_agent_endpoints_require_agent_role(client, db, ticket):
    make_user(db, "member@x.com")
    res = client.post("/agent/send-resolution", json={
        "agent_email": "member@x.com", "ticket_id": "QX-AGENT-1", "final_solution": "x",
    })
    assert res.status_code == 403


def test_agent_validate_then_send(client, db, ticket, fake_groq, sent_emails):
    make_user(db, ADMIN, role="Admin")
    fake_groq(lambda prompt, model: scores(0.92))

    val = client.post("/agent/validate-solution", json={
        "agent_email": ADMIN, "ticket_id": "QX-AGENT-1", "draft_solution": "1. Refund today",
        "steps": [{"step": "Check payment", "status": "done"}, "Issue refund"],
    })
    assert val.status_code == 200
    assert val.json()["approval_status"] == "approved"  # was always "rejected" before the await fix

    sent = client.post("/agent/send-resolution", json={
        "agent_email": ADMIN, "ticket_id": "QX-AGENT-1", "final_solution": "1. Refund today",
        "steps": ["Check payment", "Issue refund"],
    })
    assert sent.status_code == 200
    assert sent.json()["status"] == "delivered"

    db.expire_all()
    complaint = db.query(models.Complaint).filter_by(ticket_id="QX-AGENT-1").one()
    assert complaint.is_resolved is True
    assert any(e["to"] == "u@x.com" for e in sent_emails)


def test_agent_can_send_without_validating(client, db, ticket, sent_emails):
    make_user(db, "agent@x.com", is_agent=True)
    res = client.post("/agent/send-resolution", json={
        "agent_email": "agent@x.com", "ticket_id": "QX-AGENT-1", "final_solution": "Done",
    })
    assert res.status_code == 200


def test_agent_unknown_ticket_404(client, db):
    make_user(db, ADMIN, role="Admin")
    res = client.post("/agent/send-resolution", json={
        "agent_email": ADMIN, "ticket_id": "NOPE", "final_solution": "x",
    })
    assert res.status_code == 404


def test_agent_queue_and_resolutions_list(client, db, ticket):
    make_user(db, ADMIN, role="Admin")
    queue = client.get(f"/agent/complaints/queue?agent_email={ADMIN}")
    assert queue.status_code == 200
    assert "QX-AGENT-1" in queue.text
    assert client.get(f"/agent/resolutions?agent_email={ADMIN}").status_code == 200


def test_normalize_steps():
    from app.routes.agent_module import normalize_steps

    assert normalize_steps(None) is None
    assert normalize_steps([{"step": "A", "status": "done"}, " B ", None, 3]) == ["A — done", "B", "3"]
