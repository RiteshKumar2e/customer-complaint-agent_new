from app.agents.gemini_client import ask_gemini


def analyze_sentiment(text: str) -> str:
    """
    Analyzes emotional tone of complaint.
    Returns: Positive | Neutral | Negative | Angry
    """

    if not text or not text.strip():
        return "Neutral"

    text_lower = text.lower()

    # Rule-based fallback
    angry_keywords = ["worst", "terrible", "disgusting", "unacceptable", "furious", 
                     "extremely angry", "outrageous", "scam", "fraud", "lie"]
    negative_keywords = ["bad", "poor", "disappointed", "unhappy", "frustrated", 
                        "upset", "angry", "issue", "problem", "complaint"]
    positive_keywords = ["good", "great", "excellent", "thanks", "appreciate", 
                        "please", "thank you", "helpful", "resolved"]

    if any(word in text_lower for word in angry_keywords):
        return "Angry"
    if any(word in text_lower for word in negative_keywords):
        return "Negative"
    if any(word in text_lower for word in positive_keywords):
        return "Positive"

    # If no keywords match, use Gemini for more nuanced analysis
    prompt = f"""
Analyze the emotional sentiment of this text in ONE word only:
Positive, Neutral, Negative, or Angry

Text:
{text}

Return only ONE word.
"""

    try:
        result = ask_gemini(prompt).strip()
        allowed = {"Positive", "Neutral", "Negative", "Angry"}
        return result if result in allowed else "Neutral"
    except Exception:
        return "Neutral"

