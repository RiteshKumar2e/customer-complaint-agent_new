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

async def run_agent_pipeline(text: str, user_language: str = 'english'):
    return await run_agentic_loop(text, user_language=user_language, iterations=0)

async def run_agentic_loop(text: str, user_language: str = 'english', iterations: int = 0):
    """
    Optimized AI Orchestration Engine - Faster processing with essential agents only.
    Features: Anomaly Detection and RAG Support.
    """
    if not text or not text.strip():
        raise ValueError("Empty complaint text")

    steps = []
    
    # Phase 0: Security & Integrity (Anomaly Detection) - Quick check
    is_anomaly = await check_anomaly(text)
    if is_anomaly:
        steps.append({"step": "Security Check", "status": "Anomaly Detected", "risk": "High"})
    else:
        steps.append({"step": "Security Check", "status": "Verified", "risk": "Low"})

    # Phase 1: Context Identification - Parallel execution for speed
    task1 = classify_complaint(text)
    task2 = detect_priority(text)
    task3 = analyze_sentiment(text)
    
    category, priority, sentiment = await asyncio.gather(task1, task2, task3)
    steps.append({"step": "Context Identified", "category": category, "priority": priority, "sentiment": sentiment})

    # Phase 2: Knowledge Augmentation (RAG) - Quick lookup
    kb_context = await get_kb_context(category, text)
    steps.append({"step": "Knowledge Base Polled", "source": "Internal Policy DB"})

    # Phase 3: Resolution Generation - Parallel execution
    task4 = generate_response(category, f"Context: {kb_context}\nComplaint: {text}", user_language)
    task5 = suggest_solution(category, text, user_language)
    task6 = find_similar_complaints(text, category)
    
    response, solution, similar = await asyncio.gather(task4, task5, task6)
    steps.append({"step": "Resolutions Generated", "status": "Done"})

    # Phase 4: Action recommendation (fast, rule-based)
    action = recommend_action(priority)
    satisfaction = await predict_satisfaction(response, priority, category)
    
    steps.append({
        "step": "Processing Complete", 
        "status": "Success"
    })

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
        "agentic_refinement": False
    }
