from app.agents.gemini_client import ask_gemini


def predict_satisfaction(response: str, priority: str, category: str) -> str:
    """
    Predicts likelihood customer will be satisfied with proposed response.
    Returns: High | Medium | Low
    """

    if not response or not response.strip():
        return "Low"

    # Rule-based fallback
    if priority == "High":
        if any(word in response.lower() for word in ["immediately", "urgent", "escalate", "manager"]):
            return "High"
        else:
            return "Low"

    if any(word in response.lower() for word in ["apology", "sorry", "will help", "resolve", "fix", "refund", "compensation"]):
        satisfaction = "High"
    elif any(word in response.lower() for word in ["will investigate", "review", "pending"]):
        satisfaction = "Medium"
    else:
        satisfaction = "Low"

    # Use Gemini for more sophisticated analysis
    prompt = f"""
Based on this customer complaint and our response, predict customer satisfaction level.

Response: {response}
Priority: {priority}
Category: {category}

Return ONE word only: High, Medium, or Low

Consider: Is the response empathetic? Does it offer concrete solutions? Is it timely?
"""

    try:
        result = ask_gemini(prompt).strip()
        allowed = {"High", "Medium", "Low"}
        return result if result in allowed else satisfaction

    except Exception:
        return satisfaction

