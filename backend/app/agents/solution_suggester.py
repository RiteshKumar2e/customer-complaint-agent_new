import sys
import os
from app.agents.gemini_client import async_ask_gemini
from app.agents.language_detector import get_language_instruction

# Import LOCAL LLM
try:
    from app.agents.local_llm import generate_local_response
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False

# Category-specific fallback solutions
CATEGORY_SOLUTIONS = {
    "Billing": {
        'english': "We'll review your billing and process any refund within 24-48 hours. Our billing team will contact you.",
        'hinglish': "Hum aapke billing check karenge aur 24-48 hours mein refund process karenge. Team aapse contact karegi.",
        'hindi': "हम 24-48 घंटों में बिलिंग चेक करके रिफंड प्रोसेस करेंगे।"
    },
    "Technical": {
        'english': "Our technical team will investigate and provide a fix within 24 hours. We'll keep you updated.",
        'hinglish': "Humari technical team investigate karegi aur 24 hours mein fix provide karegi. Updates milte rahenge.",
        'hindi': "तकनीकी टीम 24 घंटों में समाधान देगी।"
    },
    "Delivery": {
        'english': "We apologize for the delay. We're tracking your order and will ensure priority delivery within 12 hours.",
        'hinglish': "Delay ke liye maafi. Hum order track kar rahe hain aur 12 hours mein priority delivery ensure karenge.",
        'hindi': "देरी के लिए क्षमा। 12 घंटों में प्राथमिकता डिलीवरी होगी।"
    },
    "Service": {
        'english': "We're sorry for the inconvenience. Our service team will reach out within 24 hours to resolve this personally.",
        'hinglish': "Inconvenience ke liye maafi. Service team 24 hours mein personally contact karegi.",
        'hindi': "असुविधा के लिए खेद। 24 घंटों में टीम संपर्क करेगी।"
    },
    "Security": {
        'english': "Your security is our priority. Our team is investigating immediately and will contact you within 6 hours.",
        'hinglish': "Aapki security priority hai. Team turant investigate kar rahi hai, 6 hours mein update milega.",
        'hindi': "सुरक्षा प्राथमिकता है। 6 घंटों में अपडेट मिलेगा।"
    },
    "Other": {
        'english': "Thank you for reaching out. Our support team will review your case and respond within 24 hours.",
        'hinglish': "Contact karne ke liye dhanyavaad. Support team 24 hours mein respond karegi.",
        'hindi': "संपर्क के लिए धन्यवाद। 24 घंटों में जवाब मिलेगा।"
    }
}

async def suggest_solution(category: str, text: str, user_language: str = None) -> str:
    if not text or not text.strip():
        return "Please contact our support team for assistance."

    # Auto-detect language
    if user_language is None:
        from app.agents.language_detector import detect_language
        user_language = detect_language(text)

    # Get language instruction
    language_instruction = get_language_instruction(user_language)

    # SMART, ADAPTIVE PROMPT
    prompt = f"""You are a helpful customer support agent. Analyze this complaint and provide an appropriate solution.

COMPLAINT: "{text}"
CATEGORY: {category}
LANGUAGE: {user_language.upper()}

{language_instruction}

IMPORTANT RULES:
1. Understand the complaint severity and complexity
2. For SIMPLE issues: Give a brief, direct solution (2-3 sentences)
3. For COMPLEX issues: Provide detailed steps with timelines
4. Write in PLAIN TEXT - NO markdown formatting, NO ** stars, NO bullet points
5. Write naturally like a human support agent
6. Be specific to THIS exact complaint
7. Include realistic timelines (hours/days)
8. Write ENTIRELY in {user_language.upper()} language

EXAMPLES:

Simple Issue:
Complaint: "My order is late"
Solution: "We apologize for the delay. Your order is being expedited and will reach you within 24 hours. You'll receive a tracking update shortly."

Complex Issue:
Complaint: "I was charged twice and my account is locked"
Solution: "We sincerely apologize for this issue. Here's how we'll resolve it: First, our billing team will immediately review the duplicate charge and process a refund within 24 hours. Second, we'll unlock your account within 2 hours and send you confirmation. Third, we'll credit compensation to your account within 48 hours. You'll receive updates at each step via email."

NOW ANALYZE THE COMPLAINT AND PROVIDE AN APPROPRIATE SOLUTION:"""
    
    # Try Gemini AI
    try:
        result = await async_ask_gemini(prompt)
        if result and result.strip():
            # Clean up any markdown formatting
            cleaned = result.strip()
            cleaned = cleaned.replace('**', '')  # Remove bold markers
            cleaned = cleaned.replace('##', '')  # Remove headers
            cleaned = cleaned.replace('###', '')
            cleaned = cleaned.replace('####', '')
            # Remove bullet points at start of lines
            lines = cleaned.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    line = line[1:].strip()
                if line.startswith('Step ') and ':' in line:
                    # Convert "Step 1: Action" to "First, Action"
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        line = parts[1].strip()
                cleaned_lines.append(line)
            cleaned = ' '.join(cleaned_lines)
            return cleaned
    except Exception as e:
        print(f"Gemini solution failed: {e}")
    
    # Try Local LLM
    if LOCAL_LLM_AVAILABLE:
        try:
            local_solution = generate_local_response(f"Solve this {category} complaint: {text[:200]}")
            if local_solution and len(local_solution) > 30:
                return local_solution
        except Exception as e:
            print(f"Local LLM failed: {e}")
    
    # Fallback
    category_fallbacks = CATEGORY_SOLUTIONS.get(category, CATEGORY_SOLUTIONS["Other"])
    return category_fallbacks.get(user_language, category_fallbacks.get('english', ''))
