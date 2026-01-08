from app.agents.gemini_client import async_ask_gemini

async def predict_satisfaction(response: str, priority: str, category: str) -> str:
    if not response or not response.strip():
        return "Low"

    # Layer 1: Mathematical Decision Matrix (Statistical ML)
    # Why? Priority and response length have a strong statistical correlation with satisfaction.
    # High-priority issues with very short responses often correlate to low satisfaction.
    score = 0
    if len(response.split()) > 30: score += 2 # Detailed responses are better
    if priority == "Low": score += 1 # Low priority is easier to satisfy
    if priority == "High": score -= 1 # High priority users are harder to satisfy
    
    layer1_prediction = "Medium"
    if score >= 2: layer1_prediction = "High"
    if score < 0: layer1_prediction = "Low"

    # Layer 2: Contextual AI (LLM)
    prompt = f"""Based on this customer complaint and our response, predict customer satisfaction level.
Response: {response}
Priority: {priority}
Category: {category}
Baseline Expectation: {layer1_prediction}

Return ONE word only: High, Medium, or Low"""
    try:
        result = await async_ask_gemini(prompt)
        allowed = {"High", "Medium", "Low"}
        filtered = result.strip().split('\n')[0].strip()
        return filtered if filtered in allowed else layer1_prediction
    except:
        return layer1_prediction
