import asyncio

import pytest

from app.services.multi_model_validator import MultiModelValidator
from qf_testutils import scores

COMPLAINT = {"category": "Billing", "priority": "High", "subject": "Refund", "description": "No refund yet"}


def run(coro):
    return asyncio.run(coro)


def test_awaits_async_groq_client_and_approves_good_solution(fake_groq):
    # Regression: the client call used to be missing `await`, so every model
    # "failed" and confidence was always 0.
    completions = fake_groq(lambda prompt, model: scores(0.95))
    result = run(MultiModelValidator().validate_solution(COMPLAINT, "Refund issued in 3 days"))

    assert result["approval_status"] == "approved"
    assert result["confidence_score"] == pytest.approx(0.95)
    n = len(MultiModelValidator().validation_models)
    assert len(result["validation_results"]) == n
    assert len(completions.calls) == n


@pytest.mark.parametrize("value, status", [(0.95, "approved"), (0.7, "needs_revision"), (0.3, "rejected")])
def test_approval_thresholds(fake_groq, value, status):
    fake_groq(lambda prompt, model: scores(value))
    assert run(MultiModelValidator().validate_solution(COMPLAINT, "x"))["approval_status"] == status


def test_failing_models_are_ignored(fake_groq):
    def scorer(prompt, model):
        return RuntimeError("model decommissioned") if model != "openai/gpt-oss-120b" else scores(0.9)

    fake_groq(scorer)
    result = run(MultiModelValidator().validate_solution(COMPLAINT, "x"))
    assert [r["model"] for r in result["validation_results"]] == ["openai/gpt-oss-120b"]
    assert result["approval_status"] == "approved"


def test_invalid_json_counts_as_failure(fake_groq):
    fake_groq(lambda prompt, model: "not json at all")
    result = run(MultiModelValidator().validate_solution(COMPLAINT, "x"))
    assert result["approval_status"] == "rejected"
    assert result["confidence_score"] == 0.0


def test_no_groq_client_rejects(monkeypatch):
    from app.agents.groq_client import groq_client

    monkeypatch.setattr(groq_client, "client", None)
    result = run(MultiModelValidator().validate_solution(COMPLAINT, "x"))
    assert result["approval_status"] == "rejected"
    assert "error" in result


def test_keeps_partial_results_on_timeout(fake_groq, monkeypatch):
    validator = MultiModelValidator()
    original_wait = asyncio.wait

    async def short_wait(tasks, timeout=None):
        return await original_wait(tasks, timeout=0.2)

    monkeypatch.setattr(asyncio, "wait", short_wait)

    completions = fake_groq(lambda prompt, model: scores(0.9))
    fast_create = completions.create

    async def create(**kwargs):
        if kwargs["model"] == "qwen/qwen3.8-27b":
            await asyncio.sleep(5)
        return await fast_create(**kwargs)

    completions.create = create
    result = run(validator.validate_solution(COMPLAINT, "x"))
    assert len(result["validation_results"]) == len(validator.validation_models) - 1
    assert result["approval_status"] == "approved"


@pytest.mark.parametrize("raw, expected", [
    (0.8, 0.8), ("0.5", 0.5), (8, 0.8), (85, 0.85), (-1, 0.0), ("bad", 0.0), (None, 0.0),
])
def test_normalize_score(raw, expected):
    assert MultiModelValidator._normalize_score(raw) == pytest.approx(expected)


def test_ten_point_scale_is_normalized(fake_groq):
    fake_groq(lambda prompt, model: scores(9))
    assert run(MultiModelValidator().validate_solution(COMPLAINT, "x"))["confidence_score"] == pytest.approx(0.9)


def test_recommendations_flag_weak_criteria():
    validator = MultiModelValidator()
    results = [{"model": "m", "scores": {**scores(0.9), "safety": 0.4}, "passed": False}]
    consensus = validator.calculate_consensus(results)
    recs = validator.generate_recommendations(results, consensus)
    assert any("Safety" in r for r in recs)
