from app.agents.gemini_client import async_ask_gemini

async def predict_satisfaction(response: str, priority: str, category: str) -> str:
    if not response or not response.strip():
        return "Low"

    prompt = f"""Based on this customer complaint and our response, predict customer satisfaction level.
Response: {response}
Priority: {priority}
Category: {category}
Return ONE word only: High, Medium, or Low"""
    try:
        result = await async_ask_gemini(prompt)
        allowed = {"High", "Medium", "Low"}
        return result.strip() if result.strip() in allowed else "Medium"
    except:
        return "Medium"
