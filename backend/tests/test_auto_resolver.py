"""Auto-resolution: only low-risk, high-confidence drafts are sent without a human."""
import asyncio

from sqlalchemy import select

from app.db import models
from app.db.database import get_ist_time
from app.services import auto_resolver as ar_module
from app.services.auto_resolver import AutoResolver
from qf_testutils import make_user, scores


def complaint(db, **kw):
    user = make_user(db, f"u{get_ist_time().timestamp()}@x.com")
    data = dict(ticket_id=f"QX-{id(kw)}-{len(kw)}", user_id=user.id, name="U", email=user.email, subject="Late parcel",
                description="My parcel is late", category="Delivery", priority="Low", sentiment="Neutral",
                solution="1. We will track the parcel.\n2. Update you within 24 hours.", status="open")
    data.update(kw)
    c = models.Complaint(**data)
    db.add(c)
    db.commit()
    return c


def run(cid):
    asyncio.run(AutoResolver().process_complaint(cid, delay=0))


def test_low_risk_high_confidence_is_sent(db, fake_groq, outbox, monkeypatch):
    make_user(db, "admin@x.com", role="admin")
    fake_groq(lambda prompt, model: scores(0.95))
    sent = []
    monkeypatch.setattr(ar_module.email_service, "send_agent_resolution", lambda **kw: sent.append(kw))
    c = complaint(db)
    run(c.id)
    db.expire_all()
    c = db.get(models.Complaint, c.id)
    assert c.status == "resolved" and sent and sent[0]["ticket_id"] == c.ticket_id
    res = db.execute(select(models.AgentResolution)).scalar_one()
    assert res.status == "delivered" and not res.requires_approval


def test_flagged_complaint_waits_for_human_even_with_high_confidence(db, fake_groq, monkeypatch):
    fake_groq(lambda prompt, model: scores(0.99))
    sent = []
    monkeypatch.setattr(ar_module.email_service, "send_agent_resolution", lambda **kw: sent.append(kw))
    c = complaint(db, category="Security", priority="High", requires_human_review=True,
                  review_reason="security-related complaint")
    run(c.id)
    db.expire_all()
    c = db.get(models.Complaint, c.id)
    assert c.status == "awaiting_approval" and not sent
    res = db.execute(select(models.AgentResolution)).scalar_one()
    assert res.status == "pending_approval" and res.requires_approval


def test_low_confidence_stays_draft(db, fake_groq, monkeypatch):
    fake_groq(lambda prompt, model: scores(0.3))
    monkeypatch.setattr(ar_module, "complete", _fail)
    sent = []
    monkeypatch.setattr(ar_module.email_service, "send_agent_resolution", lambda **kw: sent.append(kw))
    c = complaint(db)
    run(c.id)
    db.expire_all()
    assert db.get(models.Complaint, c.id).status == "open" and not sent
    assert db.execute(select(models.AgentResolution)).scalar_one().status == "draft"


def test_human_action_wins(db, fake_groq, monkeypatch):
    fake_groq(lambda prompt, model: scores(0.99))
    sent = []
    monkeypatch.setattr(ar_module.email_service, "send_agent_resolution", lambda **kw: sent.append(kw))
    c = complaint(db, status="in_progress")
    run(c.id)
    assert not sent and db.execute(select(models.AgentResolution)).first() is None


def test_validator_unavailable_keeps_draft(db, monkeypatch):
    from app.agents.groq_client import groq_client
    monkeypatch.setattr(groq_client, "client", None)
    sent = []
    monkeypatch.setattr(ar_module.email_service, "send_agent_resolution", lambda **kw: sent.append(kw))
    c = complaint(db)
    run(c.id)
    db.expire_all()
    assert db.get(models.Complaint, c.id).status == "open" and not sent


async def _fail(*a, **k):
    from app.agents.llm import LLMUnavailable
    raise LLMUnavailable("down")
