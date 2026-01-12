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
    
    # Build enhanced prompt
    prompt = f"""You are a SENIOR TECHNICAL SOLUTIONS ARCHITECT with expertise in customer issue resolution.

🎯 TASK: Generate a detailed, actionable solution plan

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLAINT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Category: {category}
Priority: {priority}
Language: {user_language.upper()}
SLA Timeline: {sla}
Complaint: "{complaint}"

{solution_examples}

{standard_solutions}

🌐 LANGUAGE REQUIREMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{language_instruction}

CRITICAL: Respond in {user_language.upper()} language only!

📋 SOLUTION FRAMEWORK (Include ALL 5 steps):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. IMMEDIATE ACTION (What to do in next 1 hour)
   - First emergency step
   - Who will handle it
   - Expected immediate outcome

2. ROOT CAUSE INVESTIGATION (Next 2-6 hours)
   - What to check/analyze
   - Tools/systems to use
   - Data to collect

3. PERMANENT FIX (Within SLA timeline)
   - Specific technical/process fix
   - Implementation steps
   - Testing/verification

4. CUSTOMER COMMUNICATION (Throughout process)
   - What to tell customer now
   - Update frequency
   - Contact method

5. PREVENTION & COMPENSATION (After resolution)
   - How to prevent recurrence
   - What to offer customer
   - Follow-up plan

EXAMPLE FORMAT (Hinglish):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. IMMEDIATE ACTION: Customer ka account temporarily secure kar do aur unauthorized sessions terminate karo. Security team ko immediately notify karo.

2. ROOT CAUSE: Login logs aur IP addresses check karo. Suspicious activity patterns identify karo. Last 7 days ka activity audit karo.

3. PERMANENT FIX: Password reset force karo, 2FA enable karo, aur security alerts setup karo. 24 hours mein complete security audit karo.

4. COMMUNICATION: Customer ko immediately email aur SMS bhejo ki account secure kar diya gaya hai. Har 6 hours mein update do.

5. PREVENTION: Security monitoring enhance karo, login alerts enable karo, aur customer ko 1 month free premium security service do.

NOW GENERATE THE SOLUTION:
Write a detailed 5-step solution plan in {user_language.upper()} language.

SOLUTION:"""

    try:
        solution = await async_ask_gemini(prompt)
        if solution and len(solution) > 100:
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
    
    # Ultimate fallback with detailed steps
    kb = KNOWLEDGE_BASE.get(category, {})
    solutions = kb.get('solutions', [])
    
    if language == 'hinglish':
        fallback = f"**{category} Issue Resolution Plan:**\n\n"
        fallback += "1. IMMEDIATE ACTION: Customer ka case high priority pe mark karo aur dedicated team assign karo.\n\n"
        fallback += "2. INVESTIGATION: Issue ko detail mein analyze karo aur root cause identify karo.\n\n"
        fallback += "3. SOLUTION: "
        if solutions:
            fallback += f"{solutions[0]} implement karo.\n\n"
        else:
            fallback += "Appropriate fix apply karo aur testing karo.\n\n"
        fallback += "4. COMMUNICATION: Customer ko regular updates do (har 6-12 hours mein).\n\n"
        fallback += "5. FOLLOW-UP: Resolution ke baad customer satisfaction confirm karo aur compensation offer karo."
    
    elif language == 'hindi':
        fallback = f"**{category} समस्या समाधान योजना:**\n\n"
        fallback += "1. तत्काल कार्रवाई: ग्राहक के मामले को उच्च प्राथमिकता पर चिह्नित करें।\n\n"
        fallback += "2. जांच: समस्या का विस्तार से विश्लेषण करें।\n\n"
        fallback += "3. समाधान: उपयुक्त सुधार लागू करें।\n\n"
        fallback += "4. संचार: ग्राहक को नियमित अपडेट दें।\n\n"
        fallback += "5. अनुवर्ती: समाधान के बाद संतुष्टि की पुष्टि करें।"
    
    else:  # English
        fallback = f"**{category} Issue Resolution Plan:**\n\n"
        fallback += "1. IMMEDIATE ACTION: Mark customer's case as high priority and assign dedicated team.\n\n"
        fallback += "2. INVESTIGATION: Analyze the issue in detail and identify root cause.\n\n"
        fallback += "3. SOLUTION: "
        if solutions:
            fallback += f"{solutions[0]}\n\n"
        else:
            fallback += "Implement appropriate fix and test thoroughly.\n\n"
        fallback += "4. COMMUNICATION: Provide regular updates to customer (every 6-12 hours).\n\n"
        fallback += "5. FOLLOW-UP: Confirm customer satisfaction after resolution and offer compensation."
    
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
