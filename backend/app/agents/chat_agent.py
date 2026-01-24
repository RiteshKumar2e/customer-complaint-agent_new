from app.agents.gemini_client import async_ask_gemini
from app.services.rag_engine import rag_engine
from app.agents.orchestrator import run_agent_pipeline
from app.agents.language_detector import detect_language, get_language_instruction, get_language_example
import sys
import os
import asyncio

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import CLASSIFICATION_EXAMPLES, SENTIMENT_EXAMPLES, RESPONSE_TEMPLATES
except ImportError:
    CLASSIFICATION_EXAMPLES = ""
    SENTIMENT_EXAMPLES = ""
    RESPONSE_TEMPLATES = {}

# 🚀 HIGH-PERFORMANCE IN-MEMORY CACHE (Nanosecond retrieval)
_chat_cache = {}
CACHE_MAX_SIZE = 1000

# 📚 LOCAL FAQ KNOWLEDGE BASE (Zero-Latency Answers)
FAQ_KB = {
    "features": {
        "english": "Quickfix offers AI categorization, priority detection, sentiment analysis, real-time response generation, and 24/7 automated support tracking.",
        "hinglish": "Quickfix features mein AI classification, urgent priority detection, emotions analysis, aur instant complaint resolution shaamil hain.",
        "hindi": "क्विकफिक्स में एआई वर्गीकरण, प्राथमिकता पहचान, भावना विश्लेषण, रीयल-टाइम प्रतिक्रिया और स्वचालित सहायता ट्रैकिंग शामिल है।"
    },
    "how_it_works": {
        "english": "Just type your complaint! Our AI agents analyze it, assign priority, and suggest a resolution in seconds.",
        "hinglish": "Bas apni complaint likhiye! Humare AI agents use analyze karke turant resolution recommend karenge.",
        "hindi": "बस अपनी शिकायत लिखें! हमारे एआई एजेंट इसका विश्लेषण करते हैं और कुछ ही सेकंड में समाधान सुझाते हैं।"
    },
    "agents": {
        "english": "We use specialized agents including Orchestrator, Classifier, Sentiment Analyzer, Priority Agent, and Responder.",
        "hinglish": "Humare paas specialized agents hain jaise Classifier, Sentiment Analyzer, aur Responder jo milkar kaam karte hain.",
        "hindi": "हम क्लासिफायर, सेंटीमेंट एनालाइजर और रिस्पॉन्डर जैसे विशेष एजेंटों का उपयोग करते हैं।"
    },
    "safe": {
        "english": "Yes, we use enterprise-grade encryption and Google OAuth 2.0 for secure access.",
        "hinglish": "Haan, Quickfix bilkul secure hai. Hum Google OAuth aur advanced encryption use karte hain.",
        "hindi": "हाँ, क्विकफिक्स सुरक्षित है। हम सुरक्षित पहुंच के लिए उन्नत एन्क्रिप्शन और Google OAuth का उपयोग करते हैं।"
    }
}

def get_fast_faq_response(msg: str, lang: str) -> str:
    """Matches highly specific keywords to internal FAQ for instant response.
    Generic 'how', 'kya', 'kaise' are filtered out to let AI handle them for better precision.
    """
    m = msg.lower()
    # Features specific match
    if any(k in m for k in ["website features", "service highlights", "app features"]):
        return FAQ_KB["features"].get(lang, FAQ_KB["features"]["english"])
    # Process specific match (only if it mentions 'Quickfix' or 'complain' explicitly)
    if any(k in m for k in ["how to complain", "complain kaise", "quickfix work", "process of quickfix"]):
        return FAQ_KB["how_it_works"].get(lang, FAQ_KB["how_it_works"]["english"])
    # Agent technical match
    if any(k in m for k in ["which agents", "which models", "ai technology", "backend ai"]):
        return FAQ_KB["agents"].get(lang, FAQ_KB["agents"]["english"])
    # Security specific match
    if any(k in m for k in ["data secure", "is it safe", "privacy policy"]):
        return FAQ_KB["safe"].get(lang, FAQ_KB["safe"]["english"])
    return None

async def handle_chat_message(message: str) -> dict:
    """
    Decides whether the message is a complaint (orchestrated) or a question.
    Optimized for 'Nano-Second' response speed using:
    1. In-memory caching
    2. Local Keyword FAQ matching
    3. Heuristic intent bypass
    """
    clean_msg = message.strip()
    msg_key = f"{clean_msg.lower()}"
    
    # 🏎️ TIER 0: CACHE HIT (Instant)
    if msg_key in _chat_cache:
        print("⚡ Cache Hit: Instant Response")
        return _chat_cache[msg_key]

    if not clean_msg:
        return {"role": "agent", "type": "info", "response": "How can I help you today?"}

    # 🌐 LANGUAGE DETECTION (Local & Fast)
    user_language = detect_language(clean_msg)
    language_instruction = get_language_instruction(user_language)

    # 🚀 TIER 1: FAST PATH (Greetings)
    greetings_keywords = ["hi", "hello", "hey", "halo", "namaste", "salaam", "test", "hn", "ji", "ok", "acha", "hmm", "yo", "morning", "night", "sup", "greeting", "namas", "namaskar"]
    if (len(clean_msg) < 4 and clean_msg.lower() in greetings_keywords) or clean_msg.lower() in greetings_keywords:
        greetings = {
            'hinglish': "Hello! Main aapki kaise help kar sakta hoon? Aap yahan apni complaint register kar sakte hain.",
            'hindi': "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ? आप अपनी शिकायत यहाँ दर्ज कर सकते हैं।",
            'mixed': "Hi! I'm here to help. Aap apni complaints ya queries batayein.",
            'english': "Hello! How can I assist you today? Feel free to file a complaint or ask about our services."
        }
        print(f"🌐 Detected Language: {user_language}")
        res = {"role": "agent", "type": "info", "response": greetings.get(user_language, greetings['english']), "language": user_language}
        _chat_cache[msg_key] = res
        return res

    # 🚀 TIER 2: LOCAL FAQ (No API latency)
    faq_res = get_fast_faq_response(clean_msg, user_language)
    if faq_res:
        res = {"role": "agent", "type": "info", "response": faq_res}
        _chat_cache[msg_key] = res
        return res

    # 🚀 TIER 3: HEURISTIC INTENT (Skip LLM for obvious complaints)
    complaint_markers = ["wrong", "issue", "bug", "broken", "failed", "error", "delay", "not working", "kharab", "galat", "problem", "paisay", "refund", "not received", "bekar"]
    if any(marker in clean_msg.lower() for marker in complaint_markers):
        intent = "COMPLAINT"
    else:
        # Fast intent detection with low timeout
        question_words = ["how", "what", "where", "who", "when", "why", "kya", "kaise", "kab", "kahan", "kyun", "kyu", "can", "is", "does", "provide"]
        contains_question = any(word in clean_msg.lower() for word in question_words) or "?" in clean_msg
        
        intent = "QUESTION"
        if not contains_question or len(clean_msg) > 60:
            try:
                # Using short timeout for intent
                intent_prompt = f"Categorize as ONE word: COMPLAINT or QUESTION. Message: {clean_msg}"
                intent_res = await asyncio.wait_for(async_ask_gemini(intent_prompt), timeout=3.0)
                intent = intent_res.upper()
            except:
                intent = "QUESTION"

    # 🚀 TIER 4: AI PROCESSING (Language-Aware & Versatile)
    if "QUESTION" in intent:
        # 🔍 TIER 3.5: RAG RETRIEVAL (Company Policies)
        policy_context = rag_engine.retrieve(clean_msg)
        
        system_persona = f"""
        You are the 'Quickfix AI Support Agent', a highly intelligent, empathetic, and professional assistant.
        Quickfix is an enterprise-grade AI system using 30+ specialized agents (Classifier, Sentiment, Priority, Solution) to resolve complaints.

        COMPANY POLICY CONTEXT (Use this if relevant):
        {policy_context}

        🔴 CRITICAL LANGUAGE MATCHING RULES (MUST FOLLOW):
        
        1. **STRICT LANGUAGE MIRRORING**: You MUST respond in the EXACT same language/pattern as the user's input. This is NON-NEGOTIABLE.
        
        2. **Language Detection & Response Pattern**:
           ✅ If user writes in ENGLISH → Respond ONLY in professional English
              Example User: "How does this work?"
              Example You: "Quickfix uses AI agents to analyze and resolve complaints automatically within seconds."
           
           ✅ If user writes in HINGLISH (Hindi in Roman script) → Respond ONLY in natural Hinglish
              Example User: "Ye kaise kaam karta hai?"
              Example You: "Quickfix AI agents use karta hai jo complaints ko analyze karke seconds mein resolve kar dete hain."
           
           ✅ If user writes in HINDI (Devanagari script) → Respond ONLY in pure Hindi
              Example User: "यह कैसे काम करता है?"
              Example You: "क्विकफिक्स एआई एजेंट का उपयोग करता है जो शिकायतों का विश्लेषण करके सेकंड में समाधान देते हैं।"
           
           ✅ If user writes in MIXED (English + Hinglish) → Respond in the same mixed pattern
              Example User: "How does ye system work?"
              Example You: "This system AI agents use karta hai to resolve complaints quickly."
        
        3. **BE DETAILED & HELPFUL**: 
           - Don't give one-liners. Provide comprehensive, helpful answers.
           - For questions like "how to file complaint", explain the full process step-by-step.
           - For "what features", list and explain key capabilities.
        
        4. **NO GENERIC RESPONSES**: 
           - Each answer should be specific to the user's exact question.
           - Avoid copy-paste boilerplate responses.
        
        5. **PERSONA**: Professional, empathetic, intelligent, and friendly.
        
        ⚠️ REMEMBER: Language matching is your TOP priority. If user speaks Hinglish, you MUST reply in Hinglish. If English, then English only.
        """
        
        answer_prompt = f"""{system_persona}
        
        🌐 DETECTED USER LANGUAGE: {user_language.upper()}
        
        USER QUESTION: {clean_msg}
        
        ⚠️ CRITICAL: Your response MUST be in {user_language.upper()} language/pattern ONLY.
        
        AI RESPONSE (Detailed, helpful, and in {user_language.upper()} language):"""
        try:
            print(f"🌐 Master AI Processing - Language: {user_language}")
            answer = await asyncio.wait_for(async_ask_gemini(answer_prompt), timeout=8.0)
            res = {"role": "agent", "type": "info", "response": answer, "language": user_language}
            _chat_cache[msg_key] = res
            return res
        except Exception as e:
            print(f"❌ AI Chat Error: {e}")
            fallback = {
                'hinglish': "Maaf kijiye, main abhi busy hoon. Aap login karke try kar sakte hain!",
                'hindi': "क्षमा करें, मैं अभी व्यस्त हूँ। कृपया लॉगिन करके पुनः प्रयास करें!",
                'english': "Apologies, I'm currently busy. Please log in and try again!"
            }
            return {"role": "agent", "type": "info", "response": fallback.get(user_language, fallback['english']), "language": user_language}

    # 🚀 TIER 5: COMPLAINT PIPELINE
    try:
        result = await asyncio.wait_for(
            run_agent_pipeline(clean_msg, user_language=user_language),
            timeout=15.0
        )
        
        category = result["category"]
        priority = result["priority"]
        templated_response = RESPONSE_TEMPLATES.get(category, {}).get(priority)
        final_response = templated_response if (templated_response and len(clean_msg) < 50) else result["response"]

        final_res = {
            "role": "agent",
            "type": "complaint",
            "category": result["category"],
            "priority": result["priority"],
            "response": final_response,
            "action": result["action"],
            "sentiment": result.get("sentiment", "Neutral"),
            "solution": result.get("solution", ""),
            "satisfaction": result.get("satisfaction", "Medium"),
            "similar_issues": result.get("similar_issues", ""),
            "steps": result.get("steps", []),
            "language": user_language
        }
        
        # Cache and rotate if full
        if len(_chat_cache) > CACHE_MAX_SIZE:
            _chat_cache.pop(next(iter(_chat_cache)))
        _chat_cache[msg_key] = final_res
        
        return final_res
    except Exception as e:
        print(f"❌ Chat Pipeline Error: {e}")
        return {"role": "agent", "type": "info", "response": "Something went wrong. Please try again."}

