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

# Category-specific professional fallback responses (multilingual)
CATEGORY_RESPONSES = {
    "Billing": {
        'english': "Thank you for contacting us about your billing concern. We understand how important accurate billing is, and we're reviewing your account details right away. Our billing team will reach out to you within 24-48 hours with a resolution.",
        'hinglish': "Aapki billing concern ke liye dhanyavaad. Hum samajhte hain ki accurate billing kitni important hai, aur hum abhi aapke account details review kar rahe hain. Humari billing team 24-48 hours mein aapse contact karegi.",
        'hindi': "आपकी बिलिंग चिंता के लिए धन्यवाद। हम समझते हैं कि सटीक बिलिंग कितनी महत्वपूर्ण है। हमारी बिलिंग टीम 24-48 घंटों में आपसे संपर्क करेगी।",
        'mixed': "Thank you for contacting. Hum aapke billing concern ko samajhte hain aur 24-48 hours mein resolve kar denge."
    },
    "Technical": {
        'english': "We appreciate you reporting this technical issue. Our technical team is investigating this matter with high priority. We'll work to provide you with a fix or workaround within 24 hours and keep you updated throughout the process.",
        'hinglish': "Is technical issue ko report karne ke liye shukriya. Humari technical team high priority se is matter ko investigate kar rahi hai. 24 hours mein fix ya workaround provide karenge aur aapko update karte rahenge.",
        'hindi': "इस तकनीकी समस्या की रिपोर्ट करने के लिए धन्यवाद। हमारी तकनीकी टीम उच्च प्राथमिकता से जांच कर रही है। 24 घंटों में समाधान मिलेगा।",
        'mixed': "Thank you for reporting. Humari technical team high priority se investigate kar rahi hai, 24 hours mein fix mil jayega."
    },
    "Delivery": {
        'english': "We sincerely apologize for any delay with your delivery. We're actively tracking your order and will prioritize its delivery. You can expect an update from our logistics team within 12 hours.",
        'hinglish': "Delivery mein delay ke liye hume sachme maafi hai. Hum actively aapke order ko track kar rahe hain aur priority delivery ensure karenge. 12 hours mein logistics team se update milega.",
        'hindi': "डिलीवरी में देरी के लिए हमें सचमुच खेद है। हम सक्रिय रूप से आपके ऑर्डर को ट्रैक कर रहे हैं। 12 घंटों में अपडेट मिलेगा।",
        'mixed': "Delivery delay ke liye sorry. Hum order track kar rahe hain, 12 hours mein update milega."
    },
    "Service": {
        'english': "Thank you for bringing this service matter to our attention. We're sorry for any inconvenience you've experienced. Our customer service team will personally reach out to you within 24 hours to ensure this is resolved to your satisfaction.",
        'hinglish': "Is service matter ko batane ke liye dhanyavaad. Inconvenience ke liye hume maafi hai. Humari customer service team 24 hours mein personally aapse contact karegi aur issue resolve karegi.",
        'hindi': "इस सेवा मामले को हमारे ध्यान में लाने के लिए धन्यवाद। असुविधा के लिए खेद है। हमारी टीम 24 घंटों में व्यक्तिगत रूप से संपर्क करेगी।",
        'mixed': "Service matter batane ke liye thank you. Inconvenience ke liye sorry, 24 hours mein personally contact karenge."
    },
    "Security": {
        'english': "Your security and privacy are our top priorities. We're taking your concern very seriously and our security team is investigating immediately. You'll receive a detailed update within 6 hours.",
        'hinglish': "Aapki security aur privacy humari top priority hai. Hum aapki concern ko bahut seriously le rahe hain aur humari security team turant investigate kar rahi hai. 6 hours mein detailed update milega.",
        'hindi': "आपकी सुरक्षा और गोपनीयता हमारी शीर्ष प्राथमिकताएं हैं। हमारी सुरक्षा टीम तुरंत जांच कर रही है। 6 घंटों में विस्तृत अपडेट मिलेगा।",
        'mixed': "Your security is our top priority. Hum bahut seriously le rahe hain, 6 hours mein detailed update milega."
    },
    "Other": {
        'english': "Thank you for contacting us. We've received your message and our support team is reviewing your case carefully. We'll respond with a solution within 24 hours.",
        'hinglish': "Humse contact karne ke liye dhanyavaad. Humne aapka message receive kar liya hai aur humari support team carefully review kar rahi hai. 24 hours mein solution ke saath respond karenge.",
        'hindi': "हमसे संपर्क करने के लिए धन्यवाद। हमने आपका संदेश प्राप्त कर लिया है। हमारी सहायता टीम 24 घंटों में समाधान प्रदान करेगी।",
        'mixed': "Contact karne ke liye thank you. Humari support team review kar rahi hai, 24 hours mein solution milega."
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
        prompt = f"""LANGUAGE DETECTED: {user_language.upper()}

{language_instruction}

You are a senior customer support specialist.

COMPLAINT CATEGORY: {category}
CUSTOMER COMPLAINT: {text}

CRITICAL LANGUAGE RULE:
- If language is 'hinglish', you MUST write in Hinglish (Hindi words in English script)
- DO NOT use pure English if language is hinglish
- Match the EXACT language style of the complaint

HINGLISH EXAMPLE (MANDATORY FORMAT):
Complaint: "Bhai bade hain to kya hua, humesha apni baatein manwaate hain"
Response: "Aapki family issue ke liye hume bahut maafi hai. Humari counseling team aapka case review kar rahi hai aur 24 hours mein aapko personalized guidance milega. Communication strategies aur boundary-setting techniques provide karenge."

ENGLISH EXAMPLE:
Complaint: "My brother dominates me"
Response: "I sincerely apologize for your family situation. Our counseling team is reviewing your case and will provide personalized guidance within 24 hours."

YOUR TASK:
Write empathetic response (2-3 sentences) in {user_language.upper()} language.

RESPONSE:"""
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

