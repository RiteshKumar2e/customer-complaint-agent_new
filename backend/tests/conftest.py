"""
Shared test setup — runs before any `app` module is imported.

* Database: a throwaway libSQL file opened through the same Turso dialect and
  migrations the app uses in production (TURSO_DATABASE_URL=file:...). The
  real-Turso checks live in test_turso_live.py and run only when
  TURSO_TEST_DATABASE_URL is set.
* No real API keys: no test can reach Groq, Gemini, Google or an SMTP server.
* Emails are captured in memory by the `outbox` fixture.
"""
import os
import re
import sys
import tempfile

_DB_DIR = tempfile.mkdtemp(prefix="quickfix-tests-")
os.environ.update({
    "TURSO_DATABASE_URL": "file:" + os.path.join(_DB_DIR, "test.db"),
    "TURSO_AUTH_TOKEN": "",
    "ENVIRONMENT": "test",
    "JWT_SECRET_KEY": "test-secret-key-for-automated-tests-only-0123456789",
    "EMAIL_TRANSPORT": "console",
    "EMAIL_OUTBOX_DIR": os.path.join(_DB_DIR, "outbox"),
    "ADMIN_NOTIFICATION_EMAIL": "ops@example.com",
    "SMTP_FROM_EMAIL": "support@example.com",
    "AUTO_RESOLVE_DELAY_SECONDS": "0",
    "GOOGLE_CLIENT_ID": "test-google-client-id",
    "FRONTEND_URL": "http://testserver-frontend",
})
for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "BREVO_API_KEY", "SMTP_HOST", "RENDER",
            "AGENT_CAN_VIEW_UNASSIGNED", "SENDER_EMAIL", "ADMIN_EMAIL"):
    os.environ[key] = ""

for heavy in ("transformers", "torch", "sentence_transformers", "tensorflow"):
    sys.modules[heavy] = None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dotenv  # noqa: E402

dotenv.load_dotenv = lambda *a, **k: False  # the developer's real .env must not leak into tests

import types  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db import models  # noqa: E402
from app.db.database import SessionLocal, engine  # noqa: E402
from app.db.migrations import run_migrations  # noqa: E402

run_migrations(engine)
_TABLES = [t.name for t in reversed(models.Base.metadata.sorted_tables) if t.name != "schema_migrations"]


@pytest.fixture(autouse=True)
def clean_state():
    with engine.begin() as conn:
        for table in _TABLES:
            conn.execute(text(f'DELETE FROM "{table}"'))
    from app.core.rate_limit import limiter

    limiter.reset()
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class Outbox(list):
    def to(self, address):
        return [m for m in self if m["to"] == address]

    def last_code(self, address):
        for message in reversed(self.to(address)):
            match = re.search(r"Your code: (\d{6})", message["text"])
            if match:
                return match.group(1)
        raise AssertionError(f"no OTP email for {address}")


@pytest.fixture
def outbox(monkeypatch):
    """Capture every outgoing email (synchronous auth mail and backgrounded notifications)."""
    from app.services import email_transport

    box = Outbox()

    def fake_send(to, subject, html, text, category="notification", retries=0):
        box.append({"to": to, "subject": subject, "html": html, "text": text, "category": category})

    monkeypatch.setattr(email_transport, "send", fake_send)
    return box


@pytest.fixture
def client(outbox, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services.auto_resolver import auto_resolver

    queued = []

    async def fake_process(complaint_id, delay=None):
        queued.append(complaint_id)

    monkeypatch.setattr(auto_resolver, "process_complaint", fake_process)
    with TestClient(app) as test_client:
        test_client.queued = queued
        test_client.outbox = outbox
        yield test_client


class FakeGroqCompletions:
    """Stands in for AsyncGroq().chat.completions; `scorer(prompt, model)` decides the reply."""

    def __init__(self, scorer):
        self.scorer = scorer
        self.calls = []

    async def create(self, **kwargs):
        import json

        self.calls.append(kwargs["model"])
        content = self.scorer(kwargs["messages"][-1]["content"], kwargs["model"])
        if isinstance(content, Exception):
            raise content
        if not isinstance(content, str):
            content = json.dumps(content)
        message = types.SimpleNamespace(content=content)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


@pytest.fixture
def fake_groq(monkeypatch):
    from app.agents.groq_client import groq_client

    def install(scorer):
        completions = FakeGroqCompletions(scorer)
        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))
        monkeypatch.setattr(groq_client, "client", client)
        monkeypatch.setattr(groq_client, "_models_discovered", True)
        return completions

    return install
