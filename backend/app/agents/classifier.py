from app.agents.gemini_client import async_ask_gemini

def fallback_classify(text: str) -> str:
    text = text.lower()
    if any(w in text for w in ["refund", "payment", "bill", "charge"]):
        return "Billing"
    if any(w in text for w in ["error", "bug", "crash", "login"]):
        return "Technical"
    if any(w in text for w in ["delivery", "delay", "shipment", "late"]):
        return "Delivery"
    if any(w in text for w in ["support", "staff", "rude", "service"]):
        return "Service"
    if any(w in text for w in ["fraud", "hack", "security", "breach"]):
        return "Security"
    return "Other"

async def classify_complaint(text: str) -> str:
    if not text or not text.strip():
        return "Other"

    prompt = f"""
Classify this complaint into ONE category only:
Billing, Technical, Delivery, Service, Security, Other

Complaint:
{text}
"""
    try:
        result = await async_ask_gemini(prompt)
        allowed = {"Billing", "Technical", "Delivery", "Service", "Security", "Other"}
        return result if result in allowed else fallback_classify(text)
    except Exception:
        return fallback_classify(text)
