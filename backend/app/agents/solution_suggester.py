from app.agents.gemini_client import ask_gemini


def suggest_solution(category: str, text: str) -> str:
    """
    Generates intelligent solution recommendations based on complaint category and content.
    Returns a practical solution string.
    """

    if not text or not text.strip():
        return "Please contact our support team for assistance."

    # Rule-based fallback solutions
    fallback_solutions = {
        "Billing": "We will review your billing records and process a refund/adjustment if needed.",
        "Technical": "Our technical team will investigate and provide a fix or workaround.",
        "Delivery": "We will trace your shipment and expedite delivery or issue a replacement.",
        "Service": "We apologize and will have a senior team member contact you personally.",
        "Security": "Your account has been secured and we will provide credit monitoring.",
        "Other": "Our team will investigate and follow up with you within 24 hours."
    }

    prompt = f"""
You are a customer service solution expert.

Based on this complaint category and details, suggest ONE specific, actionable solution.

Category: {category}
Complaint: {text}

Provide a practical, empathetic solution in 1-2 sentences.
"""

    try:
        result = ask_gemini(prompt)
        if result and result.strip():
            return result.strip()
        return fallback_solutions.get(category, fallback_solutions["Other"])

    except Exception:
        return fallback_solutions.get(category, fallback_solutions["Other"])

