from app.agents.gemini_client import async_ask_gemini
from app.agents.orchestrator import run_agent_pipeline

async def handle_chat_message(message: str) -> dict:
    """
    Decides whether the message is a complaint (orchestrated) or a question.
    Async to handle high traffic and concurrent users.
    """
    if not message.strip():
        return {"role": "agent", "type": "info", "response": "How can I help you today?"}

    intent_prompt = f"Classify the user message into ONE word: COMPLAINT or QUESTION. Message: {message}. Only return COMPLAINT or QUESTION."
    try:
        intent_res = await async_ask_gemini(intent_prompt)
        intent = intent_res.upper()
    except:
        intent = "QUESTION"

    if "QUESTION" in intent:
        answer = await async_ask_gemini(f"You are an AI assistant for a Customer Complaint Management website. Explain clearly and professionally: {message}")
        return {"role": "agent", "type": "info", "response": answer}

    # If it's a complaint, or we're unsure, run the full pipeline
    result = await run_agent_pipeline(message)
    return {
        "role": "agent",
        "type": "complaint",
        "category": result["category"],
        "priority": result["priority"],
        "response": result["response"],
        "action": result["action"],
        "sentiment": result.get("sentiment", "Neutral"),
        "solution": result.get("solution", ""),
        "satisfaction": result.get("satisfaction", "Medium"),
        "similar_issues": result.get("similar_issues", ""),
        "steps": result.get("steps", [])
    }
