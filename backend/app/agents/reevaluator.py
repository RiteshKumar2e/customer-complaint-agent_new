def reevaluate(priority, response):
    if "escalate" in response.lower():
        return "High"
    return priority
