def detect_priority(text: str) -> str:
    """
    Rule-based priority detection.
    Returns: Low | Medium | High
    """

    if not text or not text.strip():
        return "Low"

    text_lower = text.lower()

    high_keywords = [
        "urgent", "immediately", "angry", "refund", "fraud",
        "scam", "charged", "not working", "failed", "security",
        "breach", "harassment", "threat"
    ]

    medium_keywords = [
        "delay", "late", "problem", "issue", "slow",
        "pending", "confused", "not received"
    ]

    if any(word in text_lower for word in high_keywords):
        return "High"

    if any(word in text_lower for word in medium_keywords):
        return "Medium"

    return "Low"
