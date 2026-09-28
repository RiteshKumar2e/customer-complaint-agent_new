"""
Shared test setup.

Everything here runs before any `app` module is imported:
  * a throwaway SQLite database instead of Turso / complaints.db
  * no real API keys, so no test can reach Groq, Gemini or Brevo
  * the heavy local ML stacks are blocked, which is also what production sees
    (transformers/torch are not in requirements.txt), so the agents take their
    lightweight fallback paths instead of downloading 1.6 GB models
"""
import os
import sys
import tempfile

_DB_DIR = tempfile.mkdtemp(prefix="quickfix-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_DB_DIR, 'test.db')}"
os.environ.pop("TURSO_DATABASE_URL", None)
os.environ.pop("RENDER", None)
os.environ["ENVIRONMENT"] = "test"
for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "BREVO_API_KEY", "REDIS_URL"):
    os.environ[key] = ""
os.environ["AUTO_RESOLVE_DELAY_SECONDS"] = "0"

for heavy in ("transformers", "torch", "sentence_transformers", "tensorflow"):
    sys.modules[heavy] = None  # makes `import heavy` raise ImportError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# load_dotenv() inside the app must not put the developer's real keys back
import dotenv  # noqa: E402

dotenv.load_dotenv = lambda *a, **k: False

import types  # noqa: E402

import pytest  # noqa: E402

from app.db import models  # noqa: E402
from app.db.database import SessionLocal, engine  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sent_emails(monkeypatch):
    """Capture every outgoing email instead of calling Brevo."""
    from app.services.email_service import email_service

    sent = []
    monkeypatch.setattr(
        email_service, "_dispatch_api",
        lambda to, subject, html, priority=False: sent.append({"to": to, "subject": subject, "html": html}),
    )
    # The public senders start threads; run the workers inline so tests can assert
    for public, worker in (
        ("send_otp", "_worker_send_otp"),
        ("send_agent_resolution", "_worker_send_agent_resolution"),
        ("send_password_reset", "_worker_send_password_reset"),
    ):
        monkeypatch.setattr(email_service, public, getattr(email_service, worker))
    monkeypatch.setattr(email_service, "send_complaint_confirmation", lambda *a, **k: True)
    return sent


class FakeGroqCompletions:
    """Stands in for AsyncGroq().chat.completions; `scorer(solution_text)` picks the scores."""

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
    """Install a fake async Groq client; returns a setter for the scoring function."""
    from app.agents.groq_client import groq_client

    def install(scorer):
        completions = FakeGroqCompletions(scorer)
        client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))
        monkeypatch.setattr(groq_client, "client", client)
        return completions

    return install
