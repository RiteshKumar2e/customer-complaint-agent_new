from app.agents.gemini_client import async_ask_gemini

async def find_similar_complaints(text: str, category: str) -> str:
    if not text or not text.strip():
        return "No similar issues found."

    prompt = f"Based on this complaint, what are common similar issues we typically see? Category: {category} Complaint: {text}. List 2-3 similar complaint patterns we typically encounter, in brief bullet points."
    try:
        result = await async_ask_gemini(prompt)
        return result.strip() if result else "No similar issues found."
    except:
        return "No similar issues found."
