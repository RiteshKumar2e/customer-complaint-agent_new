import sys
import os
from app.agents.gemini_client import async_ask_gemini

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import SOLUTION_EXAMPLES
except ImportError:
    SOLUTION_EXAMPLES = ""

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
    try:
        result = await async_ask_gemini(prompt)
        return result.strip() if result else "Our team will investigate and follow up within 24 hours."
    except:
        return "Our team will investigate and follow up within 24 hours."
