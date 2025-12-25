from concurrent.futures import ThreadPoolExecutor
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

    # Use ThreadPoolExecutor to parallelize independent AI calls
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Phase 1: Independent agents
        future_category = executor.submit(classify_complaint, text)
        future_priority = executor.submit(detect_priority, text)
        future_sentiment = executor.submit(analyze_sentiment, text)
        future_similar = executor.submit(find_similar_complaints, text, "Other") # category placeholder

        # Wait for phase 1
        category = future_category.result()
        priority = future_priority.result()
        sentiment = future_sentiment.result()

        # Phase 2: Agents that might want category (running in parallel now that we have category)
        future_response = executor.submit(generate_response, category, text)
        future_solution = executor.submit(suggest_solution, category, text)
        future_action = executor.submit(recommend_action, priority)
        
        # Wait for phase 2
        response = future_response.result()
        solution = future_solution.result()
        action = future_action.result()
        
        # Phase 3: Dependent agents
        satisfaction = predict_satisfaction(response, priority, category)
        similar = future_similar.result() # already running, just get result

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
