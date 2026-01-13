import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from app.agents.language_detector import get_language_instruction, get_language_example

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Import LOCAL LLM (unlimited usage)
try:
    from app.agents.local_llm import generate_local_response
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    SUPPORTED_MODELS = [
        "gemini-2.0-flash",
        "gemini-exp-1206",
        "gemini-2.0-flash-lite",
        "gemini-flash-latest",
        "gemini-pro-latest"
    ]
    def initialize_best_model():
        for m_name in SUPPORTED_MODELS:
            try:
                return genai.GenerativeModel(m_name)
            except:
                continue
        return genai.GenerativeModel("gemini-2.0-flash")
    model = initialize_best_model()
else:
    model = None

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import RESPONSE_TEMPLATES
except ImportError:
    RESPONSE_TEMPLATES = {}

# Category-specific professional fallback responses (multilingual) - CONCISE VERSION
CATEGORY_RESPONSES = {
    "Billing": {
        'english': "Thank you for contacting us about your billing concern. Our billing team will review your account and reach out within 24-48 hours with a resolution.",
        'hinglish': "Aapki billing concern ke liye dhanyavaad. Humari billing team 24-48 hours mein aapke account ko review karke solution provide karegi.",
        'hindi': "आपकी बिलिंग चिंता के लिए धन्यवाद। हमारी टीम 24-48 घंटों में समाधान प्रदान करेगी।",
        'mixed': "Thank you for contacting. Hum 24-48 hours mein billing issue resolve kar denge."
    },
    "Technical": {
        'english': "We appreciate you reporting this technical issue. Our technical team is investigating with high priority and will provide a fix within 24 hours.",
        'hinglish': "Technical issue report karne ke liye shukriya. Humari team high priority se investigate kar rahi hai aur 24 hours mein fix provide karegi.",
        'hindi': "तकनीकी समस्या की रिपोर्ट के लिए धन्यवाद। हमारी टीम 24 घंटों में समाधान देगी।",
        'mixed': "Thank you for reporting. Technical team 24 hours mein fix provide karegi."
    },
    "Delivery": {
        'english': "We sincerely apologize for the delivery delay. We're tracking your order and will prioritize delivery. Expect an update within 12 hours.",
        'hinglish': "Delivery delay ke liye maafi chahte hain. Hum aapka order track kar rahe hain aur 12 hours mein update milega.",
        'hindi': "डिलीवरी में देरी के लिए खेद है। 12 घंटों में अपडेट मिलेगा।",
        'mixed': "Delivery delay ke liye sorry. 12 hours mein update milega."
    },
    "Service": {
        'english': "Thank you for bringing this to our attention. Our customer service team will personally reach out within 24 hours to resolve this.",
        'hinglish': "Is matter ko batane ke liye dhanyavaad. Humari team 24 hours mein personally contact karke issue resolve karegi.",
        'hindi': "इस मामले को बताने के लिए धन्यवाद। हमारी टीम 24 घंटों में संपर्क करेगी।",
        'mixed': "Thank you for informing. Team 24 hours mein personally contact karegi."
    },
    "Security": {
        'english': "Your security is our top priority. Our security team is investigating immediately and you'll receive an update within 6 hours.",
        'hinglish': "Aapki security humari top priority hai. Security team turant investigate kar rahi hai aur 6 hours mein update milega.",
        'hindi': "आपकी सुरक्षा हमारी प्राथमिकता है। 6 घंटों में अपडेट मिलेगा।",
        'mixed': "Your security is top priority. 6 hours mein detailed update milega."
    },
    "Other": {
        'english': "Thank you for contacting us. Our support team is reviewing your case and will respond with a solution within 24 hours.",
        'hinglish': "Contact karne ke liye dhanyavaad. Humari support team review kar rahi hai aur 24 hours mein solution provide karegi.",
        'hindi': "संपर्क के लिए धन्यवाद। हमारी टीम 24 घंटों में समाधान देगी।",
        'mixed': "Thank you for contacting. 24 hours mein solution milega."
    }
}

async def generate_response(category: str, text: str, user_language: str = None) -> str:
    if not text or not text.strip():
        fallback_msg = {
            'english': "Thank you for reaching out. We are here to help.",
            'hinglish': "Humse contact karne ke liye dhanyavaad. Hum aapki help ke liye yahan hain.",
            'hindi': "हमसे संपर्क करने के लिए धन्यवाद। हम आपकी मदद के लिए यहाँ हैं।",
            'mixed': "Thank you for reaching out. Hum help ke liye ready hain."
        }
        return fallback_msg.get(user_language or 'english', fallback_msg['english'])
    
    # AUTO-DETECT LANGUAGE if not provided
    if user_language is None:
        from app.agents.language_detector import detect_language
        user_language = detect_language(text)
        print(f"🌐 Auto-detected language: {user_language} for complaint: '{text[:50]}...'")
    
    # Get language-specific instruction
    language_instruction = get_language_instruction(user_language)
    language_example = get_language_example(user_language, 'complaint_received')
    
    # HINGLISH-SPECIFIC ENFORCEMENT
    if user_language == 'hinglish':
        hinglish_words = "hai, hain, aapka, aapke, aapki, hume, humne, humari, mera, meri, mere, kya, kaise, ke, liye, se, ko, ka, ki, mein, par, issue, problem, team, maafi, sachme, immediately, escalate, kar, diya, denge, karenge, milega, hoga"
        language_instruction = f"MANDATORY: You MUST respond in Hinglish (Hindi words in Roman/English script). Use these words: {hinglish_words}. DO NOT use pure English."
    
    # Layer 1: Try AI (Groq/Gemini - Best quality, contextual)
    if model is not None:
        prompt = f"""You are an empathetic customer support specialist. Write a SHORT, SPECIFIC response.

COMPLAINT: "{text}"
CATEGORY: {category}
LANGUAGE: {user_language.upper()}

{language_instruction}

INSTRUCTIONS:
1. Write in {user_language.upper()} language ONLY
2. Be SPECIFIC to this exact complaint (not generic)
3. Keep it SHORT (2-3 sentences maximum)
4. Show EMPATHY and acknowledge their specific concern
5. Mention next steps briefly

EXAMPLES:

Hinglish:
Complaint: "Mere red blood cells badh gaye hain"
Response: "Aapki health concern ke liye thank you. Humari Medical Support team 24 hours mein aapka case review karegi aur root cause identify karegi. Kal tak personalized report aur recommendations mil jayenge."

English:
Complaint: "My red blood cells are increased"
Response: "Thank you for sharing your health concern. Our Medical Support team will review your case within 24 hours to identify the cause. You'll receive a personalized report with recommendations by tomorrow."

NOW WRITE A CONCISE RESPONSE (2-3 sentences only):"""
        try:
            response = await model.generate_content_async(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Gemini generation error: {e}")
    
    # Layer 2: Try Local LLM (No API quota, unlimited usage)
    if LOCAL_LLM_AVAILABLE:
        try:
            local_response = generate_local_response(
                f"Write a professional customer support response for this {category} complaint: {text[:200]}"
            )
            if local_response and len(local_response) > 30:
                return local_response
        except Exception as e:
            print(f"Local LLM generation error: {e}")
    
    # Layer 3: Try training data templates
    if RESPONSE_TEMPLATES and category in RESPONSE_TEMPLATES:
        template_response = RESPONSE_TEMPLATES.get(category, {}).get("Medium")
        if template_response:
            return template_response
    
    # Layer 4: Category-specific professional fallback (Always works) - Language-aware
    category_fallbacks = CATEGORY_RESPONSES.get(category, CATEGORY_RESPONSES["Other"])
    return category_fallbacks.get(user_language, category_fallbacks.get('english', category_fallbacks['english']))

