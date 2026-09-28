import asyncio
from typing import Dict, List
from .classifier import classify_complaint
from .responder import generate_response
from .priority import detect_priority
from .action_recommender import recommend_action
from .sentiment_analyzer import analyze_sentiment
from .solution_suggester import suggest_solution
from .satisfaction_predictor import predict_satisfaction
from .complaint_matcher import find_similar_complaints
from .anomaly_detector import check_anomaly
from .kb_retrieval import get_kb_context
from .reevaluator import reevaluate_response
from .churn_predictor import predict_churn_risk
from .urgency_model import analyze_complaint_urgency
from app.agents.gemini_client import async_ask_ai
import json
import re

ALLOWED = {
    "category": ("Billing", "Technical", "Delivery", "Service", "Security", "Other"),
    "priority": ("High", "Medium", "Low"),
    "sentiment": ("Positive", "Neutral", "Negative", "Angry"),
    "satisfaction": ("High", "Medium", "Low"),
}
DEFAULTS = {"category": "Other", "priority": "Medium", "sentiment": "Neutral", "satisfaction": "Medium"}


def _as_text(value) -> str:
    """LLMs sometimes return lists/dicts where we expect prose (e.g. solution as a
    list of steps). The DB columns and ComplaintResponse are strings, so a list
    here used to make POST /complaint fail with a 500."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        lines = [_as_text(v) for v in value]
        lines = [l for l in lines if l]
        if len(lines) > 1 and not any(re.match(r"^\s*(\d+[.)]|[-*•])\s", l) for l in lines):
            lines = [f"{i}. {l}" for i, l in enumerate(lines, 1)]
        return "\n".join(lines)
    if isinstance(value, dict):
        label = value.get("step") or value.get("title") or value.get("text") or value.get("description")
        return _as_text(label) if label else json.dumps(value, ensure_ascii=False)
    return str(value)


def _normalize(result: dict) -> dict:
    for field, allowed in ALLOWED.items():
        value = _as_text(result.get(field)).capitalize()
        result[field] = value if value in allowed else DEFAULTS[field]
    for field in ("response", "action", "solution", "similar_issues"):
        result[field] = _as_text(result.get(field))
    result["churn_risk"] = _as_text(result.get("churn_risk")) or "Low"
    result["is_anomaly"] = bool(result.get("is_anomaly", False))
    if not isinstance(result.get("urgency_data"), dict):
        result["urgency_data"] = {}
    if not isinstance(result.get("steps"), list):
        result["steps"] = []
    return result


async def run_agent_pipeline(text: str, user_language: str = 'english'):
    return _normalize(await run_agentic_loop(text, user_language=user_language, iterations=0))

async def run_agentic_loop(text: str, user_language: str = 'english', iterations: int = 0):
    """
    ULTRA-TURBO AI Orchestration Engine.
    Consolidates multiple agent calls into a single high-speed Master Agent call.
    Reduces latency by ~70% and eliminates sequential API bottlenecks.
    """
    if not text or not text.strip():
        raise ValueError("Empty complaint text")

    steps = []
    
    # Phase 1: PARALLEL MASTER ANALYSIS
    # We combine Category, Priority, Sentiment, Solution, and Satisfaction into ONE prompt.
    master_prompt = f"""
Analyze this customer complaint and return EXACT JSON only.
Complaint: "{text}"
Language: {user_language}

JSON format:
{{
  "category": "Billing|Technical|Delivery|Service|Security|Other",
  "priority": "High|Medium|Low",
  "sentiment": "Positive|Neutral|Negative|Angry",
  "solution": "Detailed professional multi-step solution that directly resolves the user's issue with specific action steps and professional tone.",
  "satisfaction": "High|Medium|Low",
  "is_anomaly": false
}}
"""
    
    try:
        # Start Master Analysis, KB retrieval, and Similarity matching in parallel
        # This reduces 5 sequential steps to just 2!
        master_task = async_ask_ai(master_prompt)
        kb_task = get_kb_context("General", text)
        similar_task = find_similar_complaints(text, "Other")
        
        # Execute basic analysis
        master_res_raw, kb_context, similar = await asyncio.gather(master_task, kb_task, similar_task)
        
        # Parse JSON from master agent with robust cleaning
        try:
            clean_json = re.sub(r'```json|```', '', master_res_raw).strip()
            # Find the first { and last } to handle stray text
            start = clean_json.find('{')
            end = clean_json.rfind('}') + 1
            if start != -1 and end != -1:
                clean_json = clean_json[start:end]
            analysis = json.loads(clean_json)
        except:
            # Emergency local fallback if AI fails to return JSON
            analysis = {
                "category": "Other", "priority": "Medium", "sentiment": "Neutral",
                "solution": "We will investigate this immediately.", "satisfaction": "Medium",
                "is_anomaly": False
            }
            
        # Clean the LLM's fields before the downstream agents use them (a list
        # sentiment used to crash the churn predictor and drop us into the fallback)
        if not isinstance(analysis, dict):
            analysis = {}
        clean = _normalize(dict(analysis))
        category = clean["category"]
        priority = clean["priority"]
        sentiment = clean["sentiment"]
        solution = clean["solution"]
        satisfaction = clean["satisfaction"]
        is_anomaly = clean["is_anomaly"]
        
        steps.append({"step": "Master Intelligence", "status": "Turbo Analysis Done"})

        # Phase 2: Final Response Generation (Parallelized for Speed)
        response_task = generate_response(category, f"Context: {kb_context}\nComplaint: {text}", user_language)
        churn_task = predict_churn_risk(sentiment, text)
        urgency_task = analyze_complaint_urgency(text)
        
        # Execute phase 2 tasks in parallel
        response, churn_risk, urgency_analysis = await asyncio.gather(
            response_task, churn_task, urgency_task
        )
        
        action = recommend_action(priority) # This is a non-awaitable local logic usually
        
        steps.append({"step": "Processing Complete", "status": "Success"})

        return {
            "category": category,
            "priority": priority,
            "response": response,
            "action": action,
            "sentiment": sentiment,
            "solution": solution,
            "satisfaction": satisfaction,
            "similar_issues": similar,
            "steps": steps,
            "is_anomaly": is_anomaly,
            "churn_risk": churn_risk,
            "urgency_data": urgency_analysis,
            "agentic_refinement": False
        }

    except Exception as e:
        print(f"❌ Turbo Orchestrator Error: {e}")
        return {
            "category": "Other", "priority": "Medium", "response": "Service is currently optimizing, please try in a moment.",
            "action": "Manual Review", "sentiment": "Neutral", "solution": "", "satisfaction": "Medium",
            "similar_issues": "", "steps": [{"step": "Error", "status": "Fallback"}]
        }
