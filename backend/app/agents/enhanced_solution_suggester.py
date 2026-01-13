"""
Enhanced Solution Suggester with Advanced Training
Provides detailed, actionable solutions based on comprehensive knowledge base
"""
import sys
import os
from app.agents.gemini_client import async_ask_gemini
from app.agents.language_detector import detect_language, get_language_instruction

# Import enhanced training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from enhanced_training_data import (
        HINGLISH_COMPLAINT_EXAMPLES,
        ADVANCED_PROMPTS,
        KNOWLEDGE_BASE
    )
except ImportError:
    HINGLISH_COMPLAINT_EXAMPLES = {}
    ADVANCED_PROMPTS = {}
    KNOWLEDGE_BASE = {}


def get_solution_examples(category: str, count: int = 3):
    """Get solution examples from training data"""
    examples = HINGLISH_COMPLAINT_EXAMPLES.get(category, [])
    if not examples:
        return ""
    
    selected = examples[:count] if len(examples) >= count else examples
    
    example_text = "\n📚 SOLUTION EXAMPLES:\n\n"
    for i, ex in enumerate(selected, 1):
        example_text += f"{i}. Problem: {ex['complaint']}\n"
        example_text += f"   Solution: {ex['solution']}\n\n"
    
    return example_text


def get_standard_solutions(category: str):
    """Get standard solutions from knowledge base"""
    kb = KNOWLEDGE_BASE.get(category, {})
    solutions = kb.get('solutions', [])
    
    if not solutions:
        return ""
    
    solution_text = "\n🔧 STANDARD SOLUTIONS:\n"
    for i, sol in enumerate(solutions, 1):
        solution_text += f"{i}. {sol}\n"
    
    return solution_text


async def suggest_enhanced_solution(
    category: str,
    complaint: str,
    priority: str = "Medium",
    user_language: str = None
) -> str:
    """
    Generate detailed, actionable solution using enhanced training
    
    Args:
        category: Complaint category
        complaint: The complaint text
        priority: High, Medium, or Low
        user_language: Detected language
    
    Returns:
        Detailed solution steps in user's language
    """
    
    # Auto-detect language
    if user_language is None:
        user_language = detect_language(complaint)
    
    # Get solution examples and standard solutions
    solution_examples = get_solution_examples(category, count=3)
    standard_solutions = get_standard_solutions(category)
    
    # Get language instruction
    language_instruction = get_language_instruction(user_language)
    
    # Get SLA timeline
    kb = KNOWLEDGE_BASE.get(category, {})
    sla = kb.get('sla', {}).get(priority, "24-48 hours")
    
    # Build concise, actionable prompt
    prompt = f"""You are an expert customer support specialist. Generate a CONCISE, SPECIFIC solution.

COMPLAINT: "{complaint}"
CATEGORY: {category}
PRIORITY: {priority}
TIMELINE: {sla}

{solution_examples}

INSTRUCTIONS:
1. Write in {user_language.upper()} language ONLY
2. Be SPECIFIC to this exact complaint
3. Keep it SHORT and ACTIONABLE (3-4 bullet points maximum)
4. Include timeline and next steps
5. Make it PERSONAL and EMPATHETIC

{language_instruction}

FORMAT (Example for Hinglish):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Humari Medical Support team aapka case 24 hours mein review karegi aur root cause identify karegi.
• Aapko personalized report kal tak mil jayega with specific recommendations.
• Specialist consultation 3-5 business days mein schedule hoga for detailed discussion.
• 7-10 days mein follow-up review hoga to ensure your condition is improving.

NOW GENERATE A CONCISE SOLUTION (3-4 points only):"""

    try:
        solution = await async_ask_gemini(prompt)
        if solution and len(solution) > 50:  # Accept shorter, concise solutions
            return solution.strip()
    except Exception as e:
        print(f"❌ Solution generation error: {e}")
    
    # Fallback: Use training examples
    return get_fallback_solution(category, priority, user_language)


def get_fallback_solution(category: str, priority: str, language: str) -> str:
    """Get fallback solution from training data"""
    examples = HINGLISH_COMPLAINT_EXAMPLES.get(category, [])
    
    # Try to find matching priority
    for ex in examples:
        if ex.get('priority') == priority:
            return ex.get('solution', '')
    
    # Return first available
    if examples:
        return examples[0].get('solution', '')
    
    # Ultimate fallback with concise steps
    kb = KNOWLEDGE_BASE.get(category, {})
    solutions = kb.get('solutions', [])
    sla = kb.get('sla', {}).get(priority, "24-48 hours")
    
    if language == 'hinglish':
        fallback = f"**{category} Issue - Solution:**\n\n"
        fallback += f"• Humari team aapka case immediately review karegi aur {sla} mein detailed analysis provide karegi.\n"
        if solutions:
            fallback += f"• {solutions[0]}\n"
        fallback += f"• Aapko regular updates milenge aur dedicated support team assigned hogi.\n"
        fallback += f"• Issue resolve hone ke baad follow-up aur compensation discuss karenge."
    
    elif language == 'hindi':
        fallback = f"**{category} समस्या - समाधान:**\n\n"
        fallback += f"• हमारी टीम आपके मामले की तुरंत समीक्षा करेगी और {sla} में विस्तृत विश्लेषण प्रदान करेगी।\n"
        if solutions:
            fallback += f"• {solutions[0]}\n"
        fallback += f"• आपको नियमित अपडेट मिलेंगे और समर्पित सहायता टीम नियुक्त की जाएगी।\n"
        fallback += f"• समस्या हल होने के बाद फॉलो-अप और मुआवजे पर चर्चा करेंगे।"
    
    else:  # English
        fallback = f"**{category} Issue - Solution:**\n\n"
        fallback += f"• Our team will immediately review your case and provide detailed analysis within {sla}.\n"
        if solutions:
            fallback += f"• {solutions[0]}\n"
        fallback += f"• You'll receive regular updates and a dedicated support team will be assigned.\n"
        fallback += f"• After resolution, we'll discuss follow-up and compensation options."
    
    return fallback



# Backward compatibility wrapper
async def suggest_solution(category: str, text: str, user_language: str = None) -> str:
    """Wrapper for backward compatibility"""
    return await suggest_enhanced_solution(
        category=category,
        complaint=text,
        priority="Medium",
        user_language=user_language
    )
