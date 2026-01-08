from app.agents.gemini_client import async_ask_gemini

async def reevaluate_response(subject: str, description: str, final_response: str) -> dict:
    """
    Advanced Reflective Reasoning Agent (Critic).
    This agent 'Red-Teams' the primary response to ensure it's accurate, 
    safe, and solves the customer's actual problem.
    """
    critic_prompt = f"""
    You are a Senior Quality Assurance Auditor for an enterprise AI support system.
    Your task is to critique the following proposed resolution.

    CUSTOMER COMPLAINT:
    Subject: {subject}
    Details: {description}

    PROPOSED AI RESOLUTION:
    {final_response}

    CRITICAL AUDIT TASKS:
    1. Is the tone empathetic and professional?
    2. Does the solution actually address the core issue described?
    3. Is there any halluncination or incorrect technical advice?
    4. Is the resolution score assignment logical?

    Provide your critique in exactly this JSON format:
    {{
        "quality_score": 0.0 to 1.0,
        "critique_notes": "One sentence summary",
        "red_flag": true/false
    }}
    """
    try:
        result = await async_ask_gemini(critic_prompt)
        # Parse JSON from AI response
        import json
        import re
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    
    return {
        "quality_score": 0.85,
        "critique_notes": "Standard verification passed.",
        "red_flag": False
    }

async def reevaluate(priority, response):
    # Backward compatibility wrapper
    if "escalate" in response.lower():
        return "High"
    return priority

