import sys
import os
from app.agents.gemini_client import async_ask_gemini
from app.agents.language_detector import get_language_instruction, get_language_example

# Import LOCAL LLM (unlimited usage, no API key needed)
try:
    from app.agents.local_llm import generate_local_response
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import SOLUTION_EXAMPLES
except ImportError:
    SOLUTION_EXAMPLES = ""

# Category-specific fallback solutions (multilingual)
CATEGORY_SOLUTIONS = {
    "Billing": {
        'english': "We will review your billing details and process any necessary refunds within 24-48 hours. Our billing team will contact you with a resolution.",
        'hinglish': "Hum aapke billing details check karenge aur 24-48 hours mein refund process kar denge. Humari billing team aapse contact karegi.",
        'hindi': "हम आपके बिलिंग विवरण की समीक्षा करेंगे और 24-48 घंटों में आवश्यक रिफंड प्रोसेस करेंगे।",
        'mixed': "Hum aapki billing review karenge and 24-48 hours mein refund process ho jayega."
    },
    "Technical": {
        'english': "Our technical team will investigate this issue immediately. We'll provide a fix or workaround within 24 hours and keep you updated.",
        'hinglish': "Humari technical team turant is issue ko investigate karegi. 24 hours mein fix ya workaround mil jayega aur hum aapko update karte rahenge.",
        'hindi': "हमारी तकनीकी टीम तुरंत इस समस्या की जांच करेगी। 24 घंटों में समाधान मिल जाएगा।",
        'mixed': "Our technical team immediately investigate karega. 24 hours mein fix mil jayega."
    },
    "Delivery": {
        'english': "We apologize for the delay. We're tracking your order and will ensure priority delivery. You'll receive an update within 12 hours.",
        'hinglish': "Delay ke liye maafi chahte hain. Hum aapka order track kar rahe hain aur priority delivery ensure karenge. 12 hours mein update milega.",
        'hindi': "देरी के लिए हम क्षमा चाहते हैं। हम आपके ऑर्डर को ट्रैक कर रहे हैं और प्राथमिकता डिलीवरी सुनिश्चित करेंगे।",
        'mixed': "Delay ke liye sorry. Hum order track kar rahe hain and priority delivery ensure karenge."
    },
    "Service": {
        'english': "We're sorry for the inconvenience. Our service team will reach out to you within 24 hours to resolve this matter personally.",
        'hinglish': "Inconvenience ke liye hume maafi hai. Humari service team 24 hours mein aapse personally contact karegi aur issue resolve karegi.",
        'hindi': "असुविधा के लिए हमें खेद है। हमारी सेवा टीम 24 घंटों में आपसे व्यक्तिगत रूप से संपर्क करेगी।",
        'mixed': "Inconvenience ke liye sorry. Our service team 24 hours mein personally contact karega."
    },
    "Security": {
        'english': "Your security is our priority. Our security team is investigating this immediately and will contact you within 6 hours with an update.",
        'hinglish': "Aapki security humari priority hai. Humari security team turant investigate kar rahi hai aur 6 hours mein update degi.",
        'hindi': "आपकी सुरक्षा हमारी प्राथमिकता है। हमारी सुरक्षा टीम तुरंत जांच कर रही है और 6 घंटों में अपडेट देगी।",
        'mixed': "Your security is our priority. Team turant investigate kar rahi hai, 6 hours mein update milega."
    },
    "Other": {
        'english': "Thank you for bringing this to our attention. Our support team will review your case and respond with a solution within 24 hours.",
        'hinglish': "Is issue ko batane ke liye dhanyavaad. Humari support team aapka case review karegi aur 24 hours mein solution provide karegi.",
        'hindi': "इसे हमारे ध्यान में लाने के लिए धन्यवाद। हमारी सहायता टीम 24 घंटों में समाधान प्रदान करेगी।",
        'mixed': "Thank you for informing. Our support team 24 hours mein solution provide karega."
    }
}

async def suggest_solution(category: str, text: str, user_language: str = None) -> str:
    if not text or not text.strip():
        fallback_msg = {
            'english': "Please contact our support team for assistance.",
            'hinglish': "Kripya humari support team se contact karein madad ke liye.",
            'hindi': "कृपया सहायता के लिए हमारी सहायता टीम से संपर्क करें।",
            'mixed': "Please humari support team se contact karein for help."
        }
        return fallback_msg.get(user_language or 'english', fallback_msg['english'])

    # AUTO-DETECT LANGUAGE if not provided
    if user_language is None:
        from app.agents.language_detector import detect_language
        user_language = detect_language(text)
        print(f"🌐 Auto-detected language for solution: {user_language}")

    # Get language-specific instruction
    language_instruction = get_language_instruction(user_language)
    language_example = get_language_example(user_language, 'solution')

    # HINGLISH-SPECIFIC ENFORCEMENT
    if user_language == 'hinglish':
        hinglish_words = "aapke, aapka, humari, team, review, karegi, karenge, mein, hours, milega, provide, strategies, techniques, guidance, personalized, case, issue, solution, contact, escalate"
        language_instruction = f"MANDATORY: You MUST respond in Hinglish (Hindi words in Roman/English script). Use these words: {hinglish_words}. DO NOT use pure English."

    # Enhanced prompt for high-quality solutions IN USER'S LANGUAGE
    prompt = f"""LANGUAGE DETECTED: {user_language.upper()}

{language_instruction}

You are an expert customer service solution specialist.

COMPLAINT CATEGORY: {category}
CUSTOMER ISSUE: {text}

CRITICAL LANGUAGE RULE:
- If language is 'hinglish', you MUST write in Hinglish (Hindi words in English script)
- DO NOT use pure English if language is hinglish
- Match the EXACT language style of the complaint

HINGLISH SOLUTION EXAMPLE (MANDATORY FORMAT):
Complaint: "Bhai bade hain to kya hua, humesha apni baatein manwaate hain"
Solution: "Aapki family issue ka solution:
1. Humari Family Dynamics team aapka case 24 hours mein review karegi
2. Kal tak aapko personalized guidance milega on how to navigate this situation
3. Communication strategies aur boundary-setting techniques provide karenge
4. 3-5 business days mein specialist follow-up consultation schedule hoga"

ENGLISH SOLUTION EXAMPLE:
Complaint: "My brother dominates me"
Solution: "Solution for your family issue:
1. Our Family Dynamics team will review your case within 24 hours
2. You'll receive personalized guidance by tomorrow on navigating this situation
3. We'll provide communication strategies and boundary-setting techniques
4. A specialist follow-up consultation will be scheduled within 3-5 business days"

YOUR TASK:
Provide actionable solution (3-4 steps with timelines) in {user_language.upper()} language.

SOLUTION:"""
    
    # Layer 1: Try Gemini AI (Best quality, contextual)
    try:
        result = await async_ask_gemini(prompt)
        if result and result.strip():
            return result.strip()
    except Exception as e:
        print(f"Gemini solution generation failed: {e}")
    
    # Layer 2: Try Local LLM (No API quota, unlimited usage)
    if LOCAL_LLM_AVAILABLE:
        try:
            local_prompt = f"Suggest a solution for this {category} complaint: {text[:200]}"
            local_solution = generate_local_response(local_prompt)
            if local_solution and len(local_solution) > 30:
                return local_solution
        except Exception as e:
            print(f"Local LLM solution generation failed: {e}")
    
    # Layer 3: Category-specific fallback (Always works) - Language-aware
    category_fallbacks = CATEGORY_SOLUTIONS.get(category, CATEGORY_SOLUTIONS["Other"])
    return category_fallbacks.get(user_language, category_fallbacks.get('english', category_fallbacks['english']))
