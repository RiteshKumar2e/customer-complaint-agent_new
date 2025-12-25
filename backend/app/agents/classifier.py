import sys
import os
from app.agents.gemini_client import async_ask_gemini

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import CLASSIFICATION_EXAMPLES, CATEGORY_KEYWORDS
except ImportError:
    CLASSIFICATION_EXAMPLES = ""
    CATEGORY_KEYWORDS = {}

def fallback_classify(text: str) -> str:
    text = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(w in text for w in keywords):
            return cat
    return "Other"

async def classify_complaint(text: str) -> str:
    if not text or not text.strip():
        return "Other"

    # Step 1: Keyword-based heuristic (Fast)
    heuristic_res = fallback_classify(text)
    if heuristic_res != "Other":
        return heuristic_res

    # Step 2: AI-based classification (Nuanced)
    prompt = f"""
{CLASSIFICATION_EXAMPLES}

Classify this complaint into ONE category only:
Billing, Technical, Delivery, Service, Security, Other

Complaint:
{text}

Return only the category name.
"""
    try:
        result = await async_ask_gemini(prompt)
        allowed = {"Billing", "Technical", "Delivery", "Service", "Security", "Other"}
        filtered_res = result.strip().split('\n')[0].replace('.', '').strip()
        return filtered_res if filtered_res in allowed else fallback_classify(text)
    except Exception:
        return fallback_classify(text)
