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

async def run_agent_pipeline(text: str):
    """
    High-performance Async AI Orchestration Pipeline.
    Designed to handle high traffic and provide step-by-step progress.
    """
    if not text or not text.strip():
        raise ValueError("Empty complaint text")

    steps = []
    
    # Phase 1: Context Gathering (Running parallel agents)
    steps.append({"step": "Analysis Started", "status": "In Progress"})
    
    # Independent tasks
    task1 = classify_complaint(text)
    task2 = detect_priority(text)
    task3 = analyze_sentiment(text)
    
    category, priority, sentiment = await asyncio.gather(task1, task2, task3)
    steps.append({"step": "Context Identified", "category": category, "priority": priority, "sentiment": sentiment})

    # Phase 2: Generation (Using context from Phase 1)
    task4 = generate_response(category, text)
    task5 = suggest_solution(category, text)
    task6 = find_similar_complaints(text, category)
    
    response, solution, similar = await asyncio.gather(task4, task5, task6)
    steps.append({"step": "Resolutions Generated", "status": "Done"})

    # Phase 3: Final Analysis
    action = recommend_action(priority)
    satisfaction = predict_satisfaction(response, priority, category)
    steps.append({"step": "Orchestration Complete", "action": action})

    return {
        "category": category,
        "priority": priority,
        "response": response,
        "action": action,
        "sentiment": sentiment,
        "solution": solution,
        "satisfaction": satisfaction,
        "similar_issues": similar,
        "steps": steps # Return steps for UI visualization
    }
