"""Model discovery: pick from what the API key can actually use."""
import asyncio
import types

import pytest

from app.agents import gemini_client, groq_client as groq_module
from app.agents.groq_client import GroqClient, is_chat_model, rank_models

# What this account's key listed on 2026-09-28
GROQ_LISTING = [
    "allam-2-7b", "canopylabs/orpheus-arabic-saudi", "canopylabs/orpheus-v1-english",
    "meta-llama/llama-prompt-guard-2-22m", "meta-llama/llama-prompt-guard-2-86m",
    "openai/gpt-oss-120b", "openai/gpt-oss-20b", "openai/gpt-oss-safeguard-20b",
    "qwen/qwen3.8-27b", "whisper-large-v3", "whisper-large-v3-turbo",
]


def test_only_chat_models_survive_filtering():
    chat = [m for m in GROQ_LISTING if is_chat_model(m)]
    assert sorted(chat) == ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]


def test_ranking_prefers_verified_models():
    chat = [m for m in GROQ_LISTING if is_chat_model(m)]
    assert rank_models(chat) == ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]


def test_unknown_new_models_rank_by_size_after_verified_ones():
    ranked = rank_models(["openai/gpt-oss-20b", "vendor/new-8b", "vendor/new-400b"])
    assert ranked == ["openai/gpt-oss-20b", "vendor/new-400b", "vendor/new-8b"]


def test_groq_models_env_pins_order(monkeypatch):
    monkeypatch.setenv("GROQ_MODELS", "openai/gpt-oss-20b, not-listed-model")
    assert rank_models(["openai/gpt-oss-120b", "openai/gpt-oss-20b"])[0] == "openai/gpt-oss-20b"


def _client_with_listing(ids, fail=False):
    async def list_models():
        if fail:
            raise RuntimeError("network down")
        return types.SimpleNamespace(data=[types.SimpleNamespace(id=i, active=True) for i in ids])

    client = GroqClient()
    client.client = types.SimpleNamespace(models=types.SimpleNamespace(list=list_models))
    return client


def test_discovery_replaces_stale_list():
    client = _client_with_listing(GROQ_LISTING)
    client.models = ["llama-3.3-70b-versatile"]  # retired
    asyncio.run(client.discover_models())
    assert client.models == ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
    assert client.live_models == client.models


def test_discovery_failure_keeps_builtin_list():
    client = _client_with_listing([], fail=True)
    builtin = list(client.models)
    asyncio.run(client.discover_models())
    assert client.models == builtin
    assert client.live_models is None


# --- Gemini --------------------------------------------------------------------

@pytest.fixture
def fresh_gemini(monkeypatch):
    monkeypatch.setattr(gemini_client, "_gemini_models", None)
    monkeypatch.setattr(gemini_client, "_dead_models", set())
    monkeypatch.setattr(gemini_client, "GEMINI_MODEL_OVERRIDE", "")


def test_gemini_order_uses_verified_models_the_key_lists(fresh_gemini, monkeypatch):
    listed = ["models/gemini-3.8-flash", "models/gemini-flash-latest", "models/gemini-2.5-flash",
              "models/gemini-3.1-pro-preview", "models/gemini-2.5-flash-preview-tts"]
    monkeypatch.setattr(gemini_client, "_list_gemini_models", lambda: listed)
    order = asyncio.run(gemini_client.gemini_models())
    assert order[:3] == ["gemini-flash-latest", "gemini-2.5-flash", "gemini-3.8-flash"]
    assert not any("pro" in m for m in order)  # 429 quota on this plan


def test_gemini_override_goes_first(fresh_gemini, monkeypatch):
    monkeypatch.setattr(gemini_client, "GEMINI_MODEL_OVERRIDE", "gemini-3.6-flash")
    monkeypatch.setattr(gemini_client, "_list_gemini_models", lambda: [])
    assert asyncio.run(gemini_client.gemini_models())[0] == "gemini-3.6-flash"


def test_retired_gemini_model_is_skipped(fresh_gemini, monkeypatch):
    monkeypatch.setattr(gemini_client, "_list_gemini_models", lambda: ["models/gemini-flash-latest", "models/gemini-2.5-flash"])
    tried = []

    class FakeModel:
        def __init__(self, name):
            self.name = name

        async def generate_content_async(self, prompt):
            tried.append(self.name)
            if self.name == "gemini-flash-latest":
                raise RuntimeError("404 This model is no longer available")
            return types.SimpleNamespace(text="ok from " + self.name)

    monkeypatch.setattr(gemini_client.genai, "GenerativeModel", FakeModel)
    assert asyncio.run(gemini_client._generate_with_any_model("hi")) == "ok from gemini-2.5-flash"
    # second call goes straight to the working model
    tried.clear()
    asyncio.run(gemini_client._generate_with_any_model("hi"))
    assert tried == ["gemini-2.5-flash"]
