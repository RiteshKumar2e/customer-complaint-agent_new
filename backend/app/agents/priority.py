from app.agents.gemini_client import async_ask_gemini

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import PRIORITY_KEYWORDS
except ImportError:
    PRIORITY_KEYWORDS = {"High": [], "Medium": [], "Low": []}

async def detect_priority(text: str) -> str:
    """
    Hybrid priority detection.
    Layer 1: Rule-based (Fast)
    Layer 2: AI-based (Nuanced)
    """
    if not text or not text.strip():
        return "Low"

    text_lower = text.lower()
    
    # Layer 1: Check keywords first
    if any(word in text_lower for word in PRIORITY_KEYWORDS.get("High", [])):
        return "High"
    if any(word in text_lower for word in PRIORITY_KEYWORDS.get("Medium", [])):
        return "Medium"

    # Layer 2: AI Contextual check
    # Why? Keywords can't capture urgency in sentences like "I've lost all my data and I'm losing money every minute."
    prompt = f"Determine the priority (High, Medium, or Low) for this customer complaint based on urgency and potential business impact. Return only ONE word.\n\nComplaint: {text}"
    try:
        result = await async_ask_gemini(prompt)
        res = result.strip().capitalize()
        if res in ["High", "Medium", "Low"]:
            return res
    except:
        pass

    return "Low"
