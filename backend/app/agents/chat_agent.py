from app.agents.gemini_client import async_ask_gemini
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
    },
    "how_it_works": {
        "english": "Just type your complaint! Our 30+ AI agents analyze it, assign priority, and suggest a resolution in seconds.",
        "hinglish": "Bas apni complaint likhiye! Humare AI agents use analyze karke turant resolution recommend karenge.",
    },
    "agents": {
        "english": "We use 30+ specialized agents including Orchestrator, Classifier, Sentiment Analyzer, Priority Agent, and Responder.",
        "hinglish": "Humare paas 30+ agents hain jaise Classifier, Sentiment Analyzer, aur Responder jo milkar kaam karte hain.",
    },
    "safe": {
        "english": "Yes, we use enterprise-grade encryption and Google OAuth 2.0 for secure access.",
        "hinglish": "Haan, Quickfix bilkul secure hai. Hum Google OAuth aur advanced encryption use karte hain.",
    }
}

def get_fast_faq_response(msg: str, lang: str) -> str:
    """Matches keywords to internal FAQ for instant response."""
    m = msg.lower()
    if any(k in m for k in ["feature", "function", "kya kya", "highlights", "kaam", "ability"]):
        return FAQ_KB["features"].get(lang, FAQ_KB["features"]["english"])
    if any(k in m for k in ["how", "kaise", "work", "process", "chalega", "use"]):
        return FAQ_KB["how_it_works"].get(lang, FAQ_KB["how_it_works"]["english"])
    if any(k in m for k in ["agent", "technology", "tech", "model", "gemini", "ai"]):
        return FAQ_KB["agents"].get(lang, FAQ_KB["agents"]["english"])
    if any(k in m for k in ["safe", "secure", "privacy", "data", "surakshit", "protection"]):
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
    greetings_keywords = ["hi", "hello", "hey", "halo", "namaste", "salaam", "test", "hn", "ji", "ok", "acha", "hmm", "yo", "morning", "night"]
    if len(clean_msg) < 15 or clean_msg.lower() in greetings_keywords:
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

    # 🚀 TIER 4: AI PROCESSING (Language-Aware)
    if "QUESTION" in intent:
        # Enhanced prompt with strict language matching
        answer_prompt = f"""{language_instruction}

IMPORTANT: You MUST respond in the SAME language as the user's input.
- If user writes in English → Reply in English only
- If user writes in Hinglish → Reply in Hinglish only
- If user writes in Hindi → Reply in Hindi only

USER INPUT: {clean_msg}

TASK: Answer about Quickfix complaint management system briefly in the SAME language as user's input.
YOUR ANSWER:"""
        try:
            print(f"🌐 Question Language: {user_language}")
            answer = await asyncio.wait_for(async_ask_gemini(answer_prompt), timeout=5.0)
            res = {"role": "agent", "type": "info", "response": answer, "language": user_language}
            _chat_cache[msg_key] = res
            return res
        except Exception as e:
            print(f"❌ Question Error: {e}")
            fallback = {
                'hinglish': "Main thoda busy hoon, please thodi der baad try karein!",
                'hindi': "मैं थोड़ा व्यस्त हूँ, कृपया थोड़ी देर बाद प्रयास करें!",
                'english': "I'm a bit busy right now, please try again in a moment!"
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

