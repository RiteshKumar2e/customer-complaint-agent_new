"""Complaint lifecycle: submission, routing, workflow, history, attachments, notifications."""
import pytest
from sqlalchemy import select

from app.api import routes
from app.db import models
from qf_testutils import auth, fake_pipeline, make_user


@pytest.fixture
def setup(client, db, monkeypatch):
    monkeypatch.setattr(routes, "run_agent_pipeline", fake_pipeline())
    make_user(db, "cust@x.com")
    agent = make_user(db, "billing-agent@x.com", role="agent", department="Billing")
    make_user(db, "tech-agent@x.com", role="agent", department="Technical")
    make_user(db, "boss@x.com", role="admin")
    return {"cust": auth(client, "cust@x.com"), "agent": auth(client, "billing-agent@x.com"),
            "admin": auth(client, "boss@x.com"), "agent_id": agent.id}


def submit(client, headers, subject="Charged twice", description="My card was charged twice for one order."):
    res = client.post("/complaint", json={"subject": subject, "description": description}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_submission_uses_account_identity_and_routes_by_department(setup, client, db):
    data = client.post("/complaint", json={"subject": "Charged twice", "description": "My card was charged twice.",
                                           "name": "Spoofed", "email": "victim@x.com"}, headers=setup["cust"]).json()
    assert data["email"] == "cust@x.com" and data["name"] != "Spoofed"
    assert data["ticket_id"].startswith("QX-") and data["status"] == "open"
    c = db.execute(select(models.Complaint).where(models.Complaint.ticket_id == data["ticket_id"])).scalar_one()
    assert c.assigned_agent_id == setup["agent_id"]  # Billing complaint -> Billing agent
    assert c.ai_provider == "groq" and c.ai_model == "test-model"
    assert db.execute(select(models.AIExecutionLog).where(models.AIExecutionLog.complaint_id == c.id)).scalar_one()
    assert client.queued == [c.id]


def test_ticket_ids_unique(setup, client):
    ids = {submit(client, setup["cust"])["ticket_id"] for _ in range(5)}
    assert len(ids) == 5


def test_complaint_validation(setup, client):
    res = client.post("/complaint", json={"subject": "Hi", "description": "short"}, headers=setup["cust"])
    assert res.status_code == 422
    assert client.post("/complaint", json={"subject": "Valid subject", "description": "x" * 5001},
                       headers=setup["cust"]).status_code == 422


def test_staff_cannot_file_customer_complaints(setup, client):
    assert client.post("/complaint", json={"subject": "Charged twice", "description": "My card was charged twice."},
                       headers=setup["agent"]).status_code == 403


def test_list_filters_search_and_pagination(setup, client):
    for i in range(3):
        submit(client, setup["cust"], subject=f"Issue number {i}")
    res = client.get("/complaints?page=1&page_size=2", headers=setup["cust"]).json()
    assert res["total"] == 3 and len(res["items"]) == 2 and res["total_pages"] == 2
    assert client.get("/complaints?search=number 1", headers=setup["cust"]).json()["total"] == 1
    assert client.get("/complaints?status=resolved", headers=setup["cust"]).json()["total"] == 0
    assert client.get("/complaints?category=Billing", headers=setup["admin"]).json()["total"] == 3


def test_full_resolution_workflow(setup, client, db):
    t = submit(client, setup["cust"])["ticket_id"]
    h = setup["agent"]
    assert client.patch(f"/complaint/{t}/status", json={"status": "in_progress", "note": "Looking into it"},
                        headers=h).status_code == 200
    assert client.post(f"/agent/complaints/{t}/notes", json={"note": "Customer is VIP", "internal": True},
                       headers=h).status_code == 200
    assert client.post(f"/agent/complaints/{t}/notes", json={"note": "We are checking with the bank.", "internal": False},
                       headers=h).status_code == 200
    res = client.post("/agent/send-resolution", json={"ticket_id": t, "final_solution": "Refund of the duplicate charge issued.",
                                                      "steps": [{"step": "Refund", "status": "done"}]}, headers=h)
    assert res.status_code == 200
    detail = client.get(f"/complaints/{t}", headers=setup["cust"]).json()
    assert detail["status"] == "resolved" and detail["solution"].startswith("Refund")

    customer_history = [e["type"] for e in client.get(f"/complaints/{t}/history", headers=setup["cust"]).json()["events"]]
    assert "internal_note" not in customer_history and "agent_reply" in customer_history
    assert "resolution_sent" in customer_history
    staff_history = [e["type"] for e in client.get(f"/complaints/{t}/history", headers=h).json()["events"]]
    assert "internal_note" in staff_history

    res = client.post(f"/complaint/{t}/resolution-feedback", json={"is_actually_resolved": False, "user_comment": "Still charged"},
                      headers=setup["cust"])
    assert res.json()["status"] == "in_progress"
    assert client.post(f"/complaint/{t}/review", json={"rating": 4, "feedback": "ok"}, headers=setup["cust"]).status_code == 200
    assert client.post(f"/complaint/{t}/review", json={"rating": 9}, headers=setup["cust"]).status_code == 422

    notes = client.get("/notifications", headers=setup["cust"]).json()
    assert notes["unread"] >= 3
    assert client.post("/notifications/read-all", headers=setup["cust"]).status_code == 200
    assert client.get("/notifications", headers=setup["cust"]).json()["unread"] == 0


def test_invalid_status_transition(setup, client):
    t = submit(client, setup["cust"])["ticket_id"]
    res = client.patch(f"/complaint/{t}/status", json={"status": "awaiting_approval"}, headers=setup["agent"])
    assert res.status_code == 400 and res.json()["code"] == "INVALID_TRANSITION"


def test_admin_assignment(setup, client, db):
    t = submit(client, setup["cust"])["ticket_id"]
    tech = db.execute(select(models.User).where(models.User.email == "tech-agent@x.com")).scalar_one()
    assert client.patch(f"/complaints/{t}/assign", json={"agent_id": tech.id}, headers=setup["admin"]).status_code == 200
    assert client.get(f"/agent/complaints/{t}", headers=setup["agent"]).status_code == 404
    cust = db.execute(select(models.User).where(models.User.email == "cust@x.com")).scalar_one()
    assert client.patch(f"/complaints/{t}/assign", json={"agent_id": cust.id}, headers=setup["admin"]).status_code == 400


def test_sensitive_complaint_hides_ai_solution_from_customer(client, db, monkeypatch):
    monkeypatch.setattr(routes, "run_agent_pipeline", fake_pipeline(
        {"category": "Security", "priority": "High", "requires_human_review": True,
         "review_reason": "security-related complaint; high priority"}))
    make_user(db, "c2@x.com")
    data = submit(client, auth(client, "c2@x.com"), subject="Account hacked", description="Someone logged into my account.")
    assert data["requires_human_review"] is True and data["solution"] == ""


def test_attachments(setup, client):
    t = submit(client, setup["cust"])["ticket_id"]
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    res = client.post(f"/complaints/{t}/attachments", files={"file": ("../../etc/receipt.png", png, "image/png")},
                      headers=setup["cust"])
    assert res.status_code == 201 and res.json()["filename"] == "receipt.png"
    # content-type spoofing: claims PNG, is not
    res = client.post(f"/complaints/{t}/attachments", files={"file": ("x.png", b"<script>alert(1)</script>", "image/png")},
                      headers=setup["cust"])
    assert res.status_code == 415
    assert client.post(f"/complaints/{t}/attachments", files={"file": ("a.html", b"<html>", "text/html")},
                       headers=setup["cust"]).status_code == 415
    files = client.get(f"/complaints/{t}/attachments", headers=setup["cust"]).json()["attachments"]
    dl = client.get(f"/complaints/{t}/attachments/{files[0]['id']}", headers=setup["cust"])
    assert dl.status_code == 200 and dl.content == png and "attachment" in dl.headers["content-disposition"]


def test_attachment_size_limit(setup, client, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "1000")
    from app.core.config import get_settings
    get_settings.cache_clear()
    t = submit(client, setup["cust"])["ticket_id"]
    big = b"%PDF-" + b"0" * 2000
    res = client.post(f"/complaints/{t}/attachments", files={"file": ("big.pdf", big, "application/pdf")},
                      headers=setup["cust"])
    assert res.status_code == 413


def test_customer_deletes_own_complaints(setup, client):
    submit(client, setup["cust"])
    assert client.delete("/complaints", headers=setup["cust"]).json()["deleted_count"] == 1
    assert client.get("/complaints", headers=setup["cust"]).json()["total"] == 0


def test_admin_overview_and_csv(setup, client):
    submit(client, setup["cust"])
    overview = client.get("/admin/overview", headers=setup["admin"]).json()
    assert overview["complaints"]["total"] == 1 and overview["users"]["by_role"]["agent"] == 2
    csv_res = client.get("/admin/reports/complaints.csv", headers=setup["admin"])
    assert csv_res.status_code == 200 and "ticket_id" in csv_res.text.splitlines()[0]


def test_health_endpoints_accept_head(client):
    """Uptime monitors probe with HEAD; GET-only routes answered 405 in production."""
    for path in ("/", "/health", "/health/ready"):
        assert client.head(path).status_code == 200
        assert client.get(path).status_code == 200


def test_errors_are_uniform_and_leak_nothing(client):
    res = client.get("/does-not-exist")
    assert res.status_code == 404 and set(res.json()) >= {"detail", "code", "request_id"}
    assert res.headers["x-request-id"]


def test_request_size_limit(client, db):
    make_user(db, "big@x.com")
    res = client.post("/auth/login", content=b'{"email":"' + b"a" * 1_100_000 + b'"}',
                      headers={"Content-Type": "application/json"})
    assert res.status_code == 413


def test_feedback_honeypot_silently_drops_bots(client, monkeypatch):
    from app.services.email_service import email_service

    sent = []
    monkeypatch.setattr(email_service, "send_raw_to_admin", lambda *a, **k: sent.append(a) or True)
    body = {"name": "Bot", "email": "bot@example.com", "rating": 5, "message": "buy cheap stuff"}
    res = client.post("/feedback", json={**body, "website": "http://spam.example"})
    assert res.status_code == 200 and res.json()["delivered"] is False and not sent
    res = client.post("/feedback", json=body)
    assert res.status_code == 200 and sent
