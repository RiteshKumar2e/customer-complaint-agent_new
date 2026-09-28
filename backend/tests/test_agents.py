"""Tests for the AI agent modules, with every LLM call stubbed out."""
import asyncio
import json

import pytest

from app.agents import classifier, orchestrator, priority, sentiment_analyzer
from app.agents.action_recommender import recommend_action
from app.agents.churn_predictor import predict_churn_risk
from app.agents.keywords import contains_keyword
from app.agents.language_detector import detect_language
from app.agents.urgency_model import analyze_complaint_urgency


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def llm(monkeypatch):
    """Stub the LLM used by classifier/priority/sentiment; returns the list of prompts sent."""
    prompts = []

    def install(answer):
        async def fake(prompt):
            prompts.append(prompt)
            return answer
        for module in (classifier, priority, sentiment_analyzer):
            monkeypatch.setattr(module, "async_ask_gemini", fake)
        return prompts

    return install


# --- training data -----------------------------------------------------------

def test_training_data_keywords_are_loaded():
    # The file used to be named "training_data,.py", so these were always empty
    assert classifier.CATEGORY_KEYWORDS["Billing"]
    assert priority.PRIORITY_KEYWORDS["High"]
    assert sentiment_analyzer.SENTIMENT_KEYWORDS["Angry"]


@pytest.mark.parametrize("text, words, expected", [
    ("my app crashed", ["app"], True),
    ("I am happy", ["app"], False),
    ("please show me", ["how"], False),
    ("the page is not working", ["not working"], True),
    ("REFUND please", ["refund"], True),
])
def test_contains_keyword_matches_whole_words(text, words, expected):
    assert contains_keyword(text, words) is expected


# --- classifier ----------------------------------------------------------------

@pytest.mark.parametrize("text, category", [
    ("I want a refund for the duplicate payment", "Billing"),
    ("The app shows an error at login", "Technical"),
    ("My package delivery is late", "Delivery"),
    ("Your support staff was rude", "Service"),
    ("Someone tried to hack my account", "Security"),
])
def test_classifier_keyword_layer(text, category, llm):
    prompts = llm("Other")
    assert run(classifier.classify_complaint(text)) == category
    assert prompts == []  # decided without an LLM call


def test_classifier_empty_text_is_other():
    assert run(classifier.classify_complaint("   ")) == "Other"


# --- priority ------------------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("This is urgent, I was charged twice", "High"),
    ("My order is pending for a week", "Medium"),
])
def test_priority_keywords(text, expected, llm):
    prompts = llm("Low")
    assert run(priority.detect_priority(text)) == expected
    assert prompts == []


def test_priority_falls_back_to_llm(llm):
    llm("high")
    assert run(priority.detect_priority("I lose money every minute this stays down")) == "High"


def test_priority_bad_llm_answer_defaults_low(llm):
    llm("banana")
    assert run(priority.detect_priority("Just wondering about something")) == "Low"


def test_priority_empty():
    assert run(priority.detect_priority("")) == "Low"


# --- sentiment -----------------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("This is the worst service, a total scam", "Angry"),
    ("I am disappointed, the product is broken", "Negative"),
    ("Thanks, the team was very helpful", "Positive"),
])
def test_sentiment_keywords(text, expected, llm):
    llm("Neutral")
    assert run(sentiment_analyzer.analyze_sentiment(text)) == expected


def test_sentiment_empty_is_neutral():
    assert run(sentiment_analyzer.analyze_sentiment("")) == "Neutral"


# --- small deterministic agents ---------------------------------------------------

@pytest.mark.parametrize("prio, action", [
    ("High", "Escalate to human support immediately"),
    ("Medium", "Respond within 24 hours"),
    ("Low", "Auto-resolve with standard response"),
])
def test_recommend_action(prio, action):
    assert recommend_action(prio) == action


@pytest.mark.parametrize("text, lang", [
    ("My order has not arrived yet", "english"),
    ("मेरा ऑर्डर अभी तक नहीं आया", "hindi"),
    ("mera order abhi tak nahi aaya yaar", "hinglish"),
])
def test_detect_language(text, lang):
    assert detect_language(text) == lang


def test_urgency_scores_emergency_higher():
    calm = run(analyze_complaint_urgency("Could you update my address when possible"))
    urgent = run(analyze_complaint_urgency("EMERGENCY! Fix this immediately, urgent!!!"))
    assert urgent["urgency_score"] > calm["urgency_score"]


def test_churn_risk_returns_a_level():
    result = run(predict_churn_risk("Angry", "I will cancel my subscription and switch to a competitor"))
    assert result


# --- orchestrator ----------------------------------------------------------------

@pytest.fixture
def pipeline_stubs(monkeypatch):
    async def kb(category, text):
        return "KB context"

    async def similar(text, category):
        return "No similar issues"

    async def respond(category, text, lang):
        return f"Response for {category}"

    monkeypatch.setattr(orchestrator, "get_kb_context", kb)
    monkeypatch.setattr(orchestrator, "find_similar_complaints", similar)
    monkeypatch.setattr(orchestrator, "generate_response", respond)

    def set_master(answer):
        async def master(prompt):
            return answer
        monkeypatch.setattr(orchestrator, "async_ask_ai", master)

    return set_master


def test_orchestrator_parses_master_json(pipeline_stubs):
    pipeline_stubs("```json\n" + json.dumps({
        "category": "Billing", "priority": "High", "sentiment": "Angry",
        "solution": "1. Refund issued.", "satisfaction": "Low", "is_anomaly": False,
    }) + "\n```")
    result = run(orchestrator.run_agent_pipeline("I was charged twice"))

    assert result["category"] == "Billing"
    assert result["priority"] == "High"
    assert result["solution"] == "1. Refund issued."
    assert result["action"] == "Escalate to human support immediately"
    assert result["response"] == "Response for Billing"
    assert all(isinstance(s, dict) and "step" in s for s in result["steps"])


def test_orchestrator_survives_non_json_llm_output(pipeline_stubs):
    pipeline_stubs("Sorry, I cannot help with that")
    result = run(orchestrator.run_agent_pipeline("Something broke"))
    assert result["category"] == "Other"
    assert result["solution"]  # fallback text, so auto-resolution has something to work with


def test_orchestrator_rejects_empty_text():
    with pytest.raises(ValueError):
        run(orchestrator.run_agent_pipeline("  "))
