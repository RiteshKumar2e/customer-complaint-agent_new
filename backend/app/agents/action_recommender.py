def recommend_action(priority: str) -> str:
    """
    Suggests action based on priority
    """

    if priority == "High":
        return "Escalate to human support immediately"

    if priority == "Medium":
        return "Respond within 24 hours"

    return "Auto-resolve with standard response"
