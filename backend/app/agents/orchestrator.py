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

async def run_agent_pipeline(text: str):
    return await run_agentic_loop(text)

async def run_agentic_loop(text: str, iterations: int = 0):
    """
    Agentic AI Orchestration Engine with Iterative Self-Correction.
    Features: Anomaly Detection, RAG Support, and Red-Teaming Validation.
    """
    if not text or not text.strip():
        raise ValueError("Empty complaint text")

    steps = []
    
    # Phase 0: Security & Integrity (Anomaly Detection)
    is_anomaly = await check_anomaly(text)
    if is_anomaly:
        steps.append({"step": "Security Check", "status": "Anomaly Detected", "risk": "High"})
    else:
        steps.append({"step": "Security Check", "status": "Verified", "risk": "Low"})

    # Phase 1: Context Identification
    task1 = classify_complaint(text)
    task2 = detect_priority(text)
    task3 = analyze_sentiment(text)
    
    category, priority, sentiment = await asyncio.gather(task1, task2, task3)
    steps.append({"step": "Context Identified", "category": category, "priority": priority, "sentiment": sentiment})

    # Phase 2: Knowledge Augmentation (RAG)
    kb_context = await get_kb_context(category, text)
    steps.append({"step": "Knowledge Base Polled", "source": "Internal Policy DB"})

    # Phase 3: Resolution Generation
    task4 = generate_response(category, f"Context: {kb_context}\nComplaint: {text}")
    task5 = suggest_solution(category, text)
    task6 = find_similar_complaints(text, category)
    
    response, solution, similar = await asyncio.gather(task4, task5, task6)
    steps.append({"step": "Resolutions Generated", "status": "Done"})

    # Phase 4: Final Validation (Red-Teaming Critic)
    validation = await reevaluate_response("Complaint Audit", text, response)
    
    # AGENTIC SELF-CORRECTION LOOP
    # If the quality score is low or a red-flag is caught, the agent RE-ATTEMPTS generation once
    if (validation.get("quality_score", 1.0) < 0.7 or validation.get("red_flag")) and iterations < 1:
        steps.append({
            "step": "Self-Correction Triggered", 
            "reason": validation.get("critique_notes"),
            "status": "Refining..."
        })
        
        # Re-generate with critique context
        refined_prompt = f"CRITIQUE OF PREVIOUS ATTEMPT: {validation.get('critique_notes')}\n\nORIGINAL COMPLAINT: {text}\n\nFix the issues mentioned and provide a better resolution."
        response = await generate_response(category, refined_prompt)
        
        # Second Validation pass
        validation = await reevaluate_response("Complaint Audit - Final Pass", text, response)
        steps.append({"step": "Refinement Complete", "new_score": validation.get("quality_score")})
        # Note: We don't recurse here to prevent infinite loops, but we track the refinement

    action = recommend_action(priority)
    satisfaction = await predict_satisfaction(response, priority, category)
    
    steps.append({
        "step": "Quality Audit Finalized", 
        "score": validation.get("quality_score"),
        "notes": validation.get("critique_notes")
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
        "validation_audit": validation,
        "steps": steps,
        "is_anomaly": is_anomaly,
        "agentic_refinement": True if iterations > 0 or "Refinement" in steps[-2].get("step", "") else False
    }
