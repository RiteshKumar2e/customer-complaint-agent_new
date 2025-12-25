import sys
import os

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import PRIORITY_KEYWORDS
except ImportError:
    PRIORITY_KEYWORDS = {"High": [], "Medium": [], "Low": []}

async def detect_priority(text: str) -> str:
    """
    Rule-based priority detection using keywords from training data.
    Returns: Low | Medium | High
    """
    if not text or not text.strip():
        return "Low"

    text_lower = text.lower()
    
    # Check High priority keywords first
    if any(word in text_lower for word in PRIORITY_KEYWORDS.get("High", [])):
        return "High"

    # Check Medium priority keywords
    if any(word in text_lower for word in PRIORITY_KEYWORDS.get("Medium", [])):
        return "Medium"

    return "Low"
