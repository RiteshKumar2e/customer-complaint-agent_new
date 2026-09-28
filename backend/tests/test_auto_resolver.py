import asyncio

import pytest

from app.db import models
from app.db.database import get_ist_time
from app.services import auto_resolver as ar_module
from app.services.auto_resolver import AutoResolver
from qf_testutils import scores


def make_complaint(db, **overrides):
    data = dict(
        ticket_id="QX-TEST-0001", name="Asha", email="asha@example.com", subject="Refund missing",
        description="Paid twice, no refund", complaint_text="Paid twice, no refund",
        category="Billing", priority="High", sentiment="Negative",
        solution="1. We will refund the duplicate charge within 3 business days.", is_resolved=False,
    )
    data.update(overrides)
    complaint = models.Complaint(**data)
    db.add(complaint)
    db.commit()
    return complaint.id


def resolve(complaint_id):
    asyncio.run(AutoResolver().process_complaint(complaint_id, delay=0))


def reload(db, complaint_id):
    db.expire_all()
    complaint = db.get(models.Complaint, complaint_id)
    resolution = db.query(models.AgentResolution).filter_by(complaint_id=complaint_id).first()
    return complaint, resolution


def test_high_confidence_is_delivered_automatically(db, fake_groq, sent_emails):
    fake_groq(lambda prompt, model: scores(0.95))
    cid = make_complaint(db)

    resolve(cid)

    complaint, resolution = reload(db, cid)
    assert complaint.is_resolved is True
    assert resolution.status == "delivered"
    assert resolution.resolution_timestamp is not None
    assert resolution.confidence_score == pytest.approx(0.95)
    to_user = [e for e in sent_emails if e["to"] == "asha@example.com"]
    assert len(to_user) == 1 and "QX-TEST-0001" in to_user[0]["subject"]
    # one ModelValidation row per model per criterion
    assert db.query(models.ModelValidation).count() == 4 * 5


def test_weak_solution_is_improved_then_delivered(db, fake_groq, sent_emails, monkeypatch):
    fake_groq(lambda prompt, model: scores(0.95 if "IMPROVED" in prompt else 0.65))

    async def improve(prompt, max_tokens=0):
        assert "REVIEWER FEEDBACK" in prompt
        return "IMPROVED: 1. Refund issued today. 2. Confirmation mail in 24h."

    monkeypatch.setattr(ar_module.groq_client, "generate", improve)
    cid = make_complaint(db, solution="We will look into it.")

    resolve(cid)

    complaint, resolution = reload(db, cid)
    assert resolution.status == "delivered"
    assert complaint.solution.startswith("IMPROVED")
    assert resolution.final_solution.startswith("IMPROVED")
    assert any("IMPROVED" in e["html"] for e in sent_emails)


def test_low_confidence_is_held_for_human_review(db, fake_groq, sent_emails, monkeypatch):
    fake_groq(lambda prompt, model: scores(0.4))

    async def no_improvement(prompt, max_tokens=0):
        return None

    monkeypatch.setattr(ar_module.groq_client, "generate", no_improvement)
    cid = make_complaint(db)

    resolve(cid)

    complaint, resolution = reload(db, cid)
    assert complaint.is_resolved is False
    assert resolution.status == "draft"
    assert sent_emails == []


def test_improvement_that_scores_worse_is_discarded(db, fake_groq, sent_emails, monkeypatch):
    fake_groq(lambda prompt, model: scores(0.3 if "WORSE" in prompt else 0.8))

    async def worse(prompt, max_tokens=0):
        return "WORSE answer"

    monkeypatch.setattr(ar_module.groq_client, "generate", worse)
    original = "1. We will refund the duplicate charge within 3 business days."
    cid = make_complaint(db, solution=original)

    resolve(cid)

    complaint, resolution = reload(db, cid)
    assert resolution.final_solution == original
    assert resolution.status == "delivered"  # 0.8 >= default 0.75 bar


def test_validator_unavailable_holds_instead_of_sending(db, sent_emails, monkeypatch):
    monkeypatch.setattr(ar_module.groq_client, "client", None)
    cid = make_complaint(db)

    resolve(cid)

    complaint, resolution = reload(db, cid)
    assert complaint.is_resolved is False
    assert resolution.status == "draft"
    assert sent_emails == []


def test_empty_solution_is_generated(db, fake_groq, sent_emails, monkeypatch):
    fake_groq(lambda prompt, model: scores(0.95))

    async def suggest(category, text, user_language=None):
        return "1. Reset your password from Settings."

    monkeypatch.setattr(ar_module, "suggest_solution", suggest)
    cid = make_complaint(db, solution="")

    resolve(cid)

    complaint, resolution = reload(db, cid)
    assert resolution.final_solution == "1. Reset your password from Settings."
    assert complaint.is_resolved is True


def test_already_resolved_by_agent_is_skipped(db, fake_groq, sent_emails):
    completions = fake_groq(lambda prompt, model: scores(0.95))
    cid = make_complaint(db, is_resolved=True)

    resolve(cid)

    _, resolution = reload(db, cid)
    assert resolution is None
    assert completions.calls == []
    assert sent_emails == []


def test_existing_resolution_is_not_duplicated(db, fake_groq, sent_emails):
    fake_groq(lambda prompt, model: scores(0.95))
    cid = make_complaint(db)
    db.add(models.AgentResolution(
        complaint_id=cid, ticket_id="QX-TEST-0001", agent_id=1, agent_name="Human",
        draft_solution="x", final_solution="x", status="draft",
    ))
    db.commit()

    resolve(cid)

    assert db.query(models.AgentResolution).count() == 1
    assert sent_emails == []


def test_resume_pending_requeues_only_unprocessed_recent_complaints(db, monkeypatch):
    fresh = make_complaint(db, ticket_id="QX-FRESH")
    make_complaint(db, ticket_id="QX-DONE", is_resolved=True)
    make_complaint(db, ticket_id="QX-OLD", created_at=get_ist_time() - ar_module.RECOVERY_WINDOW * 2)
    has_res = make_complaint(db, ticket_id="QX-HASRES")
    db.add(models.AgentResolution(
        complaint_id=has_res, ticket_id="QX-HASRES", agent_id=1, agent_name="x",
        draft_solution="x", final_solution="x", status="draft",
    ))
    db.commit()

    resolver = AutoResolver()
    queued = []

    async def fake_process(complaint_id, delay=None):
        queued.append((complaint_id, delay))

    monkeypatch.setattr(resolver, "process_complaint", fake_process)

    async def go():
        await resolver.resume_pending()
        await asyncio.sleep(0)

    asyncio.run(go())
    assert [cid for cid, _ in queued] == [fresh]


def test_same_complaint_is_not_processed_twice_concurrently(db, fake_groq, sent_emails):
    fake_groq(lambda prompt, model: scores(0.95))
    cid = make_complaint(db)
    resolver = AutoResolver()

    async def go():
        await asyncio.gather(resolver.process_complaint(cid, delay=0), resolver.process_complaint(cid, delay=0))

    asyncio.run(go())
    assert db.query(models.AgentResolution).count() == 1
    assert len([e for e in sent_emails if e["to"] == "asha@example.com"]) == 1
