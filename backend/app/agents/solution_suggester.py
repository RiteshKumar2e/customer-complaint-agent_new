from app.agents.gemini_client import async_ask_gemini

async def suggest_solution(category: str, text: str) -> str:
    if not text or not text.strip():
        return "Please contact our support team for assistance."

    fallback_solutions = {
        "Billing": "We will review your billing records and process a refund if needed.",
        "Technical": "Our technical team will investigate and provide a fix.",
        "Delivery": "We will trace your shipment and expedite delivery.",
        "Other": "Our team will investigate and follow up within 24 hours."
    }

    prompt = f"Suggest ONE specific, actionable solution for this {category} complaint: {text}. Provide a practical, empathetic solution in 1-2 sentences."
    try:
        result = await async_ask_gemini(prompt)
        return result.strip() if result else fallback_solutions.get(category, fallback_solutions["Other"])
    except:
        return fallback_solutions.get(category, fallback_solutions["Other"])
