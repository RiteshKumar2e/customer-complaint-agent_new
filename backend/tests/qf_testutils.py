"""Helpers shared by the test modules (named to avoid clashing with a site-packages `tests`)."""
from app.core.security import hash_password
from app.db import models

PASSWORD = "Secure-pass-123"


def scores(value, feedback="ok"):
    return {
        "correctness": value, "completeness": value, "safety": value,
        "actionability": value, "clarity": value, "feedback": feedback,
    }


_phone_counter = [0]


def next_phone():
    _phone_counter[0] += 1
    return f"9{_phone_counter[0]:09d}"


def make_user(db, email, role="customer", verified=True, password=PASSWORD, phone=None, active=True,
              department=None):
    user = models.User(email=email, full_name=email.split("@")[0].title(), role=role, email_verified=verified,
                       hashed_password=hash_password(password) if password else None,
                       phone=phone or next_phone(), is_active=active, department=department)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client, email, password=PASSWORD):
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()


def auth(client, email, password=PASSWORD):
    return {"Authorization": f"Bearer {login(client, email, password)['access_token']}"}


def signup(client, email, phone=None, name="Asha Rao", password=PASSWORD):
    return client.post("/auth/register", json={"full_name": name, "email": email, "phone": phone or next_phone(),
                                               "password": password})


def register_verified(client, email, phone=None):
    res = signup(client, email, phone)
    assert res.status_code == 202, res.text
    code = client.outbox.last_code(email.strip().lower())
    res = client.post("/auth/verify-registration", json={"email": email, "otp": code})
    assert res.status_code == 200, res.text
    return res.json()


FAKE_AI = {
    "category": "Billing", "priority": "Medium", "sentiment": "Negative", "satisfaction": "Medium",
    "response": "We are sorry about the double charge and are looking into it.",
    "solution": "1. Verify the duplicate charge.\n2. Refund within 5-7 business days.",
    "action": "Respond within 24 hours", "similar_issues": "Refund Policy", "steps": [],
    "churn_risk": "Low", "urgency_data": {}, "language": "english", "fallback_used": False,
    "injection_flags": [], "requires_human_review": False, "review_reason": None,
    "ai_provider": "groq", "ai_model": "test-model", "ai_latency_ms": 12, "ai_attempts": 1, "ai_error": None,
}


def fake_pipeline(overrides=None):
    async def pipeline(text, user_language=None):
        data = dict(FAKE_AI)
        data.update(overrides or {})
        return data

    return pipeline
