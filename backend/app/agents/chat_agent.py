from app.agents.gemini_client import ask_gemini
from app.agents.orchestrator import run_agent_pipeline

def handle_chat_message(message: str) -> dict:
    """
    Decides whether the message is:
    - A general question (about website)
    - A complaint (agent pipeline)
    """

    intent_prompt = f"""
Classify the user message into ONE word:
- COMPLAINT
- QUESTION

Message:
{message}

Only return COMPLAINT or QUESTION.
"""

    intent = ask_gemini(intent_prompt).upper()

    # -----------------------------
    # GENERAL WEBSITE QUESTION
    # -----------------------------
    if "QUESTION" in intent:
        answer = ask_gemini(
            f"""
You are an AI assistant for a Customer Complaint Management website.

Explain clearly and professionally:

User question:
{message}
"""
        )

        return {
            "role": "agent",
            "type": "info",
            "response": answer
        }

    # -----------------------------
    # COMPLAINT → AGENT PIPELINE
    # -----------------------------
    result = run_agent_pipeline(message)

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
        "similar_issues": result.get("similar_issues", "")
    }
