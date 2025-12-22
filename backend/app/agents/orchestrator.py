from .classifier import classify_complaint
from .responder import generate_response
from .priority import detect_priority
from .action_recommender import recommend_action
from .sentiment_analyzer import analyze_sentiment
from .solution_suggester import suggest_solution
from .satisfaction_predictor import predict_satisfaction
from .complaint_matcher import find_similar_complaints


def run_agent_pipeline(text: str):
    if not text or not text.strip():
        raise ValueError("Empty complaint text")

    # Core agents
    category = classify_complaint(text)
    priority = detect_priority(text)
    response = generate_response(category, text)
    action = recommend_action(priority)

    # Enhanced agents
    sentiment = analyze_sentiment(text)
    solution = suggest_solution(category, text)
    satisfaction = predict_satisfaction(response, priority, category)
    similar = find_similar_complaints(text, category)

    if not all([category, priority, response, action]):
        raise ValueError("One or more agents returned empty output")

    return {
        "category": category,
        "priority": priority,
        "response": response,
        "action": action,
        "sentiment": sentiment,
        "solution": solution,
        "satisfaction": satisfaction,
        "similar_issues": similar
    }
