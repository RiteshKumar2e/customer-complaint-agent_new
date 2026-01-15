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

async def handle_chat_message(message: str) -> dict:
    """
    ULTRA-FAST Chat Handler:
    1. Local Fast-Path for greetings (0s delay)
    2. Combined Intent + Answer call (Single AI hit for Questions)
    3. Background pipeline only for complex complaints
    """
    clean_msg = message.strip()
    msg_len = len(clean_msg)
    
    if msg_len == 0:
        return {"role": "agent", "type": "info", "response": "How can I help you today?"}

    # 🌐 LANGUAGE DETECTION (Fast Regex-based)
    user_language = detect_language(clean_msg)
    lang_instr = get_language_instruction(user_language)

    # 🚀 STEP 1: LOCAL FAST-PATH (Non-AI)
    # Greetings, simple inquiries, and small talk
    greetings_map = {
        'hi': {'english': "Hello! How can I help you?", 'hinglish': "Hi! Main aapki kaise help kar sakta hoon?"},
        'hello': {'english': "Hi there! What's on your mind?", 'hinglish': "Hello! Kya help chahiye aapko?"},
        'hey': {'english': "Hey! How's it going?", 'hinglish': "Hey! Sab theek? Kaise help karoon?"},
        'thanks': {'english': "You're welcome!", 'hinglish': "Koi baat nahi! Anytime help chahiye toh batana."},
        'dhanyavad': {'hindi': "आपका स्वागत है!", 'hinglish': "Aapka swagat hai!"},
        'ok': {'english': "Great! Let me know if you need anything else.", 'hinglish': "Theek hai! Aur kuch help chahiye?"},
        'help': {'english': "I can help you file a complaint, track status, or answer questions about our services.", 'hinglish': "Kaise help karoon? Aap complaint file kar sakte hain ya platform ke baare mein puch sakte hain."}
    }
    
    msg_lower = clean_msg.lower().replace('?', '').replace('!', '')
    if msg_lower in greetings_map:
        res = greetings_map[msg_lower].get(user_language, greetings_map[msg_lower].get('english'))
        return {"role": "agent", "type": "info", "response": res}

    # 🚀 STEP 2: COMBINED INTENT & ANSWER (Single AI Call)
    # This cuts latency in half for 90% of queries
    combined_prompt = f"""{CLASSIFICATION_EXAMPLES}
User Message: {clean_msg}
Language: {user_language} ({lang_instr})

TASK:
1. Classify intent: COMPLAINT (reporting a problem) or QUESTION (asking info/chatting).
2. If intent=QUESTION, generate a high-quality, professional, and helpful response.
3. If intent=COMPLAINT, just say intent: COMPLAINT.

RESPONSE FORMAT (JSON ONLY):
{{
  "intent": "QUESTION" or "COMPLAINT",
  "response": "Your detailed answer here (if question)"
}}

Rules for Question Response:
- Be detailed and professional like an expert.
- Focus on Quickfix features: Tracking, AI Analysis, 24/7 Support.
- Match user's language exact style.
- Use bullet points if listing steps.
"""

    try:
        # High-speed call for combined processing
        ai_res_raw = await asyncio.wait_for(
            async_ask_gemini(combined_prompt),
            timeout=8.0
        )
        
        # Simple parsing (robust enough for JSON)
        import json
        try:
            # Try to find JSON block if AI adds fluff
            start = ai_res_raw.find('{')
            end = ai_res_raw.rfind('}') + 1
            if start != -1:
                ai_data = json.loads(ai_res_raw[start:end])
            else:
                ai_data = {"intent": "QUESTION", "response": ai_res_raw}
        except:
            # Fallback if AI output is weird
            if "COMPLAINT" in ai_res_raw.upper():
                ai_data = {"intent": "COMPLAINT"}
            else:
                ai_data = {"intent": "QUESTION", "response": ai_res_raw}

        if ai_data.get("intent") == "QUESTION":
            return {"role": "agent", "type": "info", "response": ai_data.get("response")}
            
    except Exception as e:
        print(f"Combined AI call failed: {e}")
        # Default to pipeline for safety if combined fails
        pass

    # 🚀 STEP 3: COMPLAINT PIPELINE (Only for actual complaints)
    try:
        result = await asyncio.wait_for(
            run_agent_pipeline(message, user_language=user_language),
            timeout=20.0
        )
        
        # Check if we have a template for this category/priority
        category = result["category"]
        priority = result["priority"]
        templated_response = RESPONSE_TEMPLATES.get(category, {}).get(priority)
        
        # If templated response exists and message is short, use it
        final_response = templated_response if (templated_response and msg_len < 50) else result["response"]

        return {
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
    except asyncio.TimeoutError:
        print("⏱️ Complaint pipeline timeout")
        timeout_responses = {
            'hinglish': "Aapki complaint process ho rahi hai. Thoda time lag raha hai. Kya aap thodi der baad try kar sakte hain?",
            'hindi': "आपकी शिकायत प्रोसेस हो रही है। थोड़ा समय लग रहा है। क्या आप थोड़ी देर बाद प्रयास कर सकते हैं?",
            'mixed': "Your complaint is being processed. Thoda delay ho raha hai. Please try again shortly.",
            'english': "Your complaint is being processed but taking longer than expected. Please try again in a moment."
        }
        return {
            "role": "agent",
            "type": "info",
            "response": timeout_responses.get(user_language, timeout_responses['english'])
        }
    except Exception as e:
        print(f"❌ Complaint pipeline failed: {e}")
        error_responses = {
            'hinglish': "Sorry, aapki complaint process karne mein issue aa raha hai. Please thodi der baad try karein.",
            'hindi': "क्षमा करें, आपकी शिकायत प्रोसेस करने में समस्या आ रही है। कृपया थोड़ी देर बाद प्रयास करें।",
            'mixed': "Sorry, complaint process mein problem hai. Please try again later.",
            'english': "I apologize, but I'm having trouble processing your complaint. Please try again shortly."
        }
        return {
            "role": "agent",
            "type": "info",
            "response": error_responses.get(user_language, error_responses['english'])
        }
