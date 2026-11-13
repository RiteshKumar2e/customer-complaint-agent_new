"""Broken access control, IDOR and privilege escalation checks."""
import pytest
from sqlalchemy import select

from app.api import routes
from app.db import models
from qf_testutils import auth, fake_pipeline, make_user


@pytest.fixture
def world(client, db, monkeypatch):
    monkeypatch.setattr(routes, "run_agent_pipeline", fake_pipeline())
    make_user(db, "alice@x.com")
    make_user(db, "bob@x.com")
    agent1 = make_user(db, "agent1@x.com", role="agent")
    make_user(db, "agent2@x.com", role="agent")
    make_user(db, "admin@x.com", role="admin")
    headers = {name: auth(client, f"{name}@x.com") for name in ("alice", "bob", "agent1", "agent2", "admin")}
    res = client.post("/complaint", json={"subject": "Double charge", "description": "I was charged twice for my order this month."},
                      headers=headers["alice"])
    assert res.status_code == 201, res.text
    ticket = res.json()["ticket_id"]
    complaint = db.execute(select(models.Complaint).where(models.Complaint.ticket_id == ticket)).scalar_one()
    complaint.assigned_agent_id = agent1.id  # deterministic assignment for the test
    db.commit()
    return {"h": headers, "ticket": ticket}


ADMIN_ENDPOINTS = [
    ("get", "/admin/overview"), ("get", "/admin/users"), ("get", "/admin/agents"), ("get", "/admin/ai/logs"),
    ("get", "/admin/ai/summary"), ("get", "/admin/audit-logs"), ("get", "/admin/login-history"),
    ("get", "/admin/login-stats"), ("get", "/admin/system"), ("get", "/admin/categories"),
    ("get", "/admin/reports/complaints.csv"),
]


@pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
def test_customer_and_agent_cannot_use_admin_endpoints(world, client, method, path):
    for who in ("alice", "agent1"):
        assert getattr(client, method)(path, headers=world["h"][who]).status_code == 403
    assert getattr(client, method)(path).status_code == 401
    assert getattr(client, method)(path, headers=world["h"]["admin"]).status_code == 200


def test_customer_cannot_see_other_customers_complaint(world, client):
    t, h = world["ticket"], world["h"]
    assert client.get(f"/complaints/{t}", headers=h["alice"]).status_code == 200
    for path in (f"/complaints/{t}", f"/complaints/{t}/history", f"/complaints/{t}/attachments"):
        assert client.get(path, headers=h["bob"]).status_code == 404
    assert client.get("/complaints", headers=h["bob"]).json()["total"] == 0
    assert client.delete(f"/complaint/{t}", headers=h["bob"]).status_code == 404
    assert client.post(f"/complaint/{t}/review", json={"rating": 1}, headers=h["bob"]).status_code == 404
    assert client.post(f"/complaint/{t}/resolution-feedback", json={"is_actually_resolved": True},
                       headers=h["bob"]).status_code == 404


def test_customer_cannot_change_status_or_assign(world, client):
    t, h = world["ticket"], world["h"]
    assert client.patch(f"/complaint/{t}/status", json={"status": "resolved"}, headers=h["alice"]).status_code == 403
    assert client.patch(f"/complaints/{t}/assign", json={"agent_id": 1}, headers=h["alice"]).status_code == 403
    assert client.post("/agent/send-resolution", json={"ticket_id": t, "final_solution": "Done, all fixed now."},
                       headers=h["alice"]).status_code == 403


def test_agent_only_sees_assigned_complaints(world, client):
    t, h = world["ticket"], world["h"]
    assert client.get(f"/agent/complaints/{t}", headers=h["agent1"]).status_code == 200
    assert client.get(f"/agent/complaints/{t}", headers=h["agent2"]).status_code == 404
    assert client.get("/agent/complaints/queue", headers=h["agent2"]).json()["total"] == 0
    assert client.get("/agent/complaints/queue", headers=h["agent1"]).json()["total"] == 1
    res = client.post("/agent/send-resolution", json={"ticket_id": t, "final_solution": "Refund issued today."},
                      headers=h["agent2"])
    assert res.status_code == 404


def test_agent_email_parameter_cannot_impersonate(world, client):
    """The old API trusted ?agent_email=; identity must come from the token only."""
    t, h = world["ticket"], world["h"]
    res = client.get(f"/agent/complaints/{t}?agent_email=agent1@x.com", headers=h["agent2"])
    assert res.status_code == 404
    assert client.get("/agent/complaints/queue?agent_email=admin@x.com").status_code == 401


def test_profile_update_cannot_escalate_role(world, client, db):
    h = world["h"]
    for field, value in (("role", "admin"), ("email", "x@y.com"), ("email_verified", True), ("is_active", True)):
        res = client.patch("/auth/me", json={field: value}, headers=h["alice"])
        assert res.status_code == 422, field
    assert client.patch("/auth/update-profile", json={"role": "Admin"}, headers=h["alice"]).status_code == 422
    db.expire_all()
    assert db.execute(select(models.User.role).where(models.User.email == "alice@x.com")).scalar_one() == "customer"


def test_profile_update_only_touches_own_account(world, client, db):
    res = client.patch("/auth/update-profile?email=bob@x.com", json={"full_name": "Hacked Name"}, headers=world["h"]["alice"])
    assert res.status_code == 200 and res.json()["email"] == "alice@x.com"
    db.expire_all()
    assert db.execute(select(models.User.full_name).where(models.User.email == "bob@x.com")).scalar_one() != "Hacked Name"


def test_profile_phone_validation_and_uniqueness(world, client, db):
    h = world["h"]
    assert client.patch("/auth/me", json={"phone": "12345"}, headers=h["alice"]).status_code == 422
    bob_phone = db.execute(select(models.User.phone).where(models.User.email == "bob@x.com")).scalar_one()
    assert client.patch("/auth/me", json={"phone": bob_phone}, headers=h["alice"]).status_code == 409
    assert client.patch("/auth/me", json={"phone": "7000000001"}, headers=h["alice"]).status_code == 200


def test_role_change_takes_effect_immediately(world, client, db):
    h = world["h"]
    agent1 = db.execute(select(models.User).where(models.User.email == "agent1@x.com")).scalar_one()
    res = client.patch(f"/admin/users/{agent1.id}", json={"role": "customer"}, headers=h["admin"])
    assert res.status_code == 200
    assert client.get("/agent/complaints/queue", headers=h["agent1"]).status_code == 401  # old token revoked


def test_admin_cannot_lock_themselves_out(world, client, db):
    admin = db.execute(select(models.User).where(models.User.email == "admin@x.com")).scalar_one()
    res = client.patch(f"/admin/users/{admin.id}", json={"role": "customer"}, headers=world["h"]["admin"])
    assert res.status_code == 400 and res.json()["code"] == "SELF_LOCKOUT"


def test_agents_cannot_delete_complaints(world, client):
    assert client.delete(f"/complaint/{world['ticket']}", headers=world["h"]["agent1"]).status_code == 403


def test_bulk_delete_is_admin_only(world, client):
    assert client.request("DELETE", "/complaints/bulk", json={"ids": [1]}, headers=world["h"]["alice"]).status_code == 403


def test_notifications_are_private(world, client, db):
    alice_notes = client.get("/notifications", headers=world["h"]["alice"]).json()["items"]
    assert alice_notes
    note_id = alice_notes[0]["id"]
    assert client.post(f"/notifications/{note_id}/read", headers=world["h"]["bob"]).status_code == 404
