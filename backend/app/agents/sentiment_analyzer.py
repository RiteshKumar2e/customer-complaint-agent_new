from app.agents.gemini_client import async_ask_gemini

async def analyze_sentiment(text: str) -> str:
    if not text or not text.strip():
        return "Neutral"

    text_lower = text.lower()
    angry_keywords = ["worst", "terrible", "disgusting", "unacceptable", "furious", "angry", "scam", "fraud"]
    if any(word in text_lower for word in angry_keywords):
        return "Angry"

    prompt = f"Analyze the emotional sentiment of this text in ONE word only: Positive, Neutral, Negative, or Angry. Text: {text}"
    try:
        result = await async_ask_gemini(prompt)
        allowed = {"Positive", "Neutral", "Negative", "Angry"}
        return result if result in allowed else "Neutral"
    except:
        return "Neutral"
