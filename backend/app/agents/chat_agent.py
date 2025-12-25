from app.agents.gemini_client import async_ask_gemini
from app.agents.orchestrator import run_agent_pipeline
import sys
import os

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import CLASSIFICATION_EXAMPLES, SENTIMENT_EXAMPLES, RESPONSE_TEMPLATES
except ImportError:
    CLASSIFICATION_EXAMPLES = ""
    SENTIMENT_EXAMPLES = ""
    RESPONSE_TEMPLATES = {}

async def handle_chat_message(message: str) -> dict:
    """
    Decides whether the message is a complaint (orchestrated) or a question.
    Async to handle high traffic and concurrent users.
    """
    msg_len = len(message.strip())
    if msg_len == 0:
        return {"role": "agent", "type": "info", "response": "How can I help you today?"}

    # Intent detection with few-shot examples from training data
    intent_prompt = f"""
{CLASSIFICATION_EXAMPLES}

Classify the user message into ONE word: COMPLAINT or QUESTION.
Message: {message}

Rules:
- If user is reporting an issue, bug, or service failure, it's a COMPLAINT.
- If user is asking HOW the site works or general info, it's a QUESTION.
- If query is very short (e.g., "Hi", "Hello", "test"), it's a QUESTION.

Only return ONE word.
"""
    try:
        intent_res = await async_ask_gemini(intent_prompt)
        intent = intent_res.upper()
    except:
        intent = "QUESTION"

    # Short query handling
    if msg_len < 10 and "COMPLAINT" not in intent:
        return {"role": "agent", "type": "info", "response": "Hello! How can I assist you today?"}

    if "QUESTION" in intent:
        # For questions, provide a concise answer if the query is short
        length_hint = "Provide a very short, 1-sentence answer." if msg_len < 30 else "Provide a clear and professional answer."
        
        answer = await async_ask_gemini(f"""
You are an AI assistant for Quickfix, a Customer Complaint Management website.
{length_hint}

User question:
{message}
""")
        return {"role": "agent", "type": "info", "response": answer}

    # If it's a complaint, run the full pipeline
    result = await run_agent_pipeline(message)
    
    # Check if we have a template for this category/priority
    category = result["category"]
    priority = result["priority"]
    templated_response = RESPONSE_TEMPLATES.get(category, {}).get(priority)
    
    # If templated response exists and message is short, use it
    final_response = templated_response if (templated_response and msg_len < 50) else result["response"]

    return {
        "role": "agent",
        "type": "complaint",
        "category": result["category"],
        "priority": result["priority"],
        "response": final_response,
        "action": result["action"],
        "sentiment": result.get("sentiment", "Neutral"),
        "solution": result.get("solution", ""),
        "satisfaction": result.get("satisfaction", "Medium"),
        "similar_issues": result.get("similar_issues", ""),
        "steps": result.get("steps", [])
    }
