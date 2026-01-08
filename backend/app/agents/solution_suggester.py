import sys
import os
from app.agents.gemini_client import async_ask_gemini

# Import LOCAL LLM (unlimited usage, no API key needed)
try:
    from app.agents.local_llm import generate_local_response
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import SOLUTION_EXAMPLES
except ImportError:
    SOLUTION_EXAMPLES = ""

# Category-specific fallback solutions
CATEGORY_SOLUTIONS = {
    "Billing": "We will review your billing details and process any necessary refunds within 24-48 hours. Our billing team will contact you with a resolution.",
    "Technical": "Our technical team will investigate this issue immediately. We'll provide a fix or workaround within 24 hours and keep you updated.",
    "Delivery": "We apologize for the delay. We're tracking your order and will ensure priority delivery. You'll receive an update within 12 hours.",
    "Service": "We're sorry for the inconvenience. Our service team will reach out to you within 24 hours to resolve this matter personally.",
    "Security": "Your security is our priority. Our security team is investigating this immediately and will contact you within 6 hours with an update.",
    "Other": "Thank you for bringing this to our attention. Our support team will review your case and respond with a solution within 24 hours."
}

async def suggest_solution(category: str, text: str) -> str:
    if not text or not text.strip():
        return "Please contact our support team for assistance."

    prompt = f"""
{SOLUTION_EXAMPLES}

You are a customer service solution expert.
Based on this complaint category and details, suggest ONE specific, actionable solution.

Category: {category}
Complaint: {text}

Provide a practical, empathetic solution in 1-2 sentences.
"""
    
    # Layer 1: Try Gemini AI (Best quality, contextual)
    try:
        result = await async_ask_gemini(prompt)
        if result and result.strip():
            return result.strip()
    except Exception as e:
        print(f"Gemini solution generation failed: {e}")
    
    # Layer 2: Try Local LLM (No API quota, unlimited usage)
    if LOCAL_LLM_AVAILABLE:
        try:
            local_prompt = f"Suggest a solution for this {category} complaint: {text[:200]}"
            local_solution = generate_local_response(local_prompt)
            if local_solution and len(local_solution) > 30:
                return local_solution
        except Exception as e:
            print(f"Local LLM solution generation failed: {e}")
    
    # Layer 3: Category-specific fallback (Always works)
    return CATEGORY_SOLUTIONS.get(category, CATEGORY_SOLUTIONS["Other"])
