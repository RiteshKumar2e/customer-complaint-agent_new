from app.agents.gemini_client import ask_gemini


def find_similar_complaints(text: str, category: str) -> str:
    """
    Identifies similar past complaints to provide consistent handling.
    Returns a summary of similar complaint patterns.
    """

    if not text or not text.strip():
        return "No similar issues found."

    prompt = f"""
Based on this complaint, what are common similar issues we typically see?

Category: {category}
Complaint: {text}

List 2-3 similar complaint patterns we typically encounter, in brief bullet points.
Keep it concise.
"""

    try:
        result = ask_gemini(prompt)
        if result and result.strip():
            return result.strip()
        return "No similar issues found."

    except Exception:
        return "No similar issues found."

