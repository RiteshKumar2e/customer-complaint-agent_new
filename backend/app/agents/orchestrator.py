"""
Complaint analysis pipeline.

What actually runs, in order:
  1. Sanitise the complaint text and check it for prompt-injection phrasing.
  2. Detect the writing language (English / Hindi / Hinglish / ...).
  3. Retrieve relevant policy snippets from the knowledge base (TF-IDF RAG).
  4. ONE structured LLM call (Groq, then Gemini) under a timeout, returning
     category / priority / sentiment / satisfaction / response / solution.
     Output must pass a strict schema; one repair retry on invalid output.
  5. If no provider produces valid output: deterministic local analysis.
  6. Local heuristics: churn risk (logistic regression), urgency (keywords +
     TextBlob polarity), recommended action from priority.
  7. Decide whether the resolution needs human approval before anything is
     sent to the customer.

The result includes provenance (provider, model, latency, fallback flag) so
it can be stored with the complaint and in ai_execution_logs.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

from app.agents import local_analysis
from app.agents.action_recommender import recommend_action
from app.agents.churn_predictor import predict_churn_risk
from app.agents.guardrails import (
    ANALYSIS_SYSTEM_PROMPT,
    OutputRejected,
    detect_injection,
    parse_analysis,
    sanitize_user_text,
    wrap_untrusted,
)
from app.agents.language_detector import detect_language
from app.agents.llm import LLMUnavailable, complete
from app.agents.urgency_model import analyze_complaint_urgency
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.rag_engine import rag_engine

logger = get_logger("app.ai.pipeline")

ALLOWED = {
    "category": ("Billing", "Technical", "Delivery", "Service", "Security", "Other"),
    "priority": ("High", "Medium", "Low"),
    "sentiment": ("Positive", "Neutral", "Negative", "Angry"),
    "satisfaction": ("High", "Medium", "Low"),
}


def review_reasons(result: Dict, injection_flags: List[str]) -> List[str]:
    """Why a human must approve before a resolution is sent to the customer."""
    reasons = []
    if injection_flags or result.get("suspicious"):
        reasons.append("possible prompt injection")
    if result.get("fallback_used"):
        reasons.append("AI unavailable - offline analysis")
    if result.get("category") == "Security":
        reasons.append("security-related complaint")
    if result.get("priority") == "High":
        reasons.append("high priority")
    if result.get("sentiment") == "Angry":
        reasons.append("angry customer")
    if result.get("churn_risk") == "Critical":
        reasons.append("critical churn risk")
    return reasons


def _policy_topics(context: str) -> str:
    topics = [line.split("]:")[0].lstrip("[") for line in context.split("\n\n") if line.startswith("[")]
    return ", ".join(topics) if topics else ""


async def _llm_analysis(text: str, language: str, kb_context: str):
    s = get_settings()
    system = ANALYSIS_SYSTEM_PROMPT.format(company=s.company_name, language=language)
    prompt = f"POLICY CONTEXT (trusted):\n{kb_context}\n\nCUSTOMER COMPLAINT (untrusted):\n{wrap_untrusted(text)}"
    first = await complete(prompt, system=system, json_mode=True, temperature=0.2)
    try:
        return parse_analysis(first.text), first, 1
    except OutputRejected as exc:
        logger.warning("AI output rejected (%s); retrying once", exc)
    repair = (prompt + "\n\nYour previous reply was not valid. Reply with ONLY the JSON object described in the "
              "output contract, using exactly the allowed enum values.")
    second = await complete(repair, system=system, json_mode=True, temperature=0.0)
    second.latency_ms += first.latency_ms
    return parse_analysis(second.text), second, 2


async def run_agent_pipeline(text: str, user_language: Optional[str] = None) -> Dict:
    started = time.perf_counter()
    clean = sanitize_user_text(text)
    if not clean:
        raise ValueError("Empty complaint text")

    injection_flags = detect_injection(text)  # raw input: sanitising first would hide delimiter attacks
    language = user_language or detect_language(clean)
    kb_context = rag_engine.retrieve(clean)
    steps = [{"step": "Input screening", "status": "flagged" if injection_flags else "clean"},
             {"step": "Knowledge base retrieval", "status": "done"}]

    provider, model, fallback_used, error, attempts = "local", local_analysis.LOCAL_MODEL_NAME, False, None, 0
    try:
        analysis, llm_result, attempts = await _llm_analysis(clean, language, kb_context)
        result = analysis.model_dump()
        provider, model = llm_result.provider, llm_result.model
        steps.append({"step": "LLM analysis", "status": f"{provider}:{model}"})
    except (LLMUnavailable, OutputRejected) as exc:
        error = str(exc)[:300]
        fallback_used = True
        result = local_analysis.analyze(clean, language)
        result["suspicious"] = False
        steps.append({"step": "LLM analysis", "status": "unavailable - offline analysis used"})

    for field, allowed in ALLOWED.items():  # belt and braces before anything is stored
        if result.get(field) not in allowed:
            result[field] = local_analysis.analyze(clean, language)[field]

    result["churn_risk"] = await predict_churn_risk(result["sentiment"], clean)
    result["urgency_data"] = await analyze_complaint_urgency(clean)
    result["action"] = recommend_action(result["priority"])
    result["similar_issues"] = _policy_topics(kb_context)
    result["language"] = language
    result["fallback_used"] = fallback_used
    reasons = review_reasons(result, injection_flags)
    result.update({
        "steps": steps + [{"step": "Review gate", "status": "human approval required" if reasons else "auto-eligible"}],
        "injection_flags": injection_flags,
        "requires_human_review": bool(reasons),
        "review_reason": "; ".join(reasons)[:255] or None,
        "ai_provider": provider,
        "ai_model": model,
        "ai_latency_ms": int((time.perf_counter() - started) * 1000),
        "ai_attempts": attempts,
        "ai_error": error,
    })
    result.pop("suspicious", None)
    return result
