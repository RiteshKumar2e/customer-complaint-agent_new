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
    Decides whether the message is a complaint (orchestrated) or a question.
    Detects user's language and responds in the SAME language.
    Guarantees High-Quality, Professional, and Detailed Responses.
    """
    clean_msg = message.strip()
    msg_len = len(clean_msg)
    if msg_len == 0:
        return {"role": "agent", "type": "info", "response": "How can I help you today?"}

    # 🌐 LANGUAGE DETECTION
    user_language = detect_language(clean_msg)
    language_instruction = get_language_instruction(user_language)
    
    print(f"🌐 Detected Language: {user_language}")

    # 🚀 STEP 1: Intent detection with few-shot examples
    intent_prompt = f"""
{CLASSIFICATION_EXAMPLES}

Classify the user message into ONE word: COMPLAINT or QUESTION.
Message: {clean_msg}

Rules:
- If user is reporting an issue, bug, or service failure, it's a COMPLAINT.
- If user is asking HOW the site works or general info, it's a QUESTION.
- If query is very short (e.g., "Hi", "Hello", "test"), it's a QUESTION.

Only return ONE word.
"""
    try:
        intent_res = await asyncio.wait_for(async_ask_gemini(intent_prompt), timeout=10.0)
        intent = intent_res.upper()
    except:
        intent = "QUESTION"

    # 🚀 STEP 2: Handle Greetings & Short Talk (Fast)
    if msg_len < 10 and "COMPLAINT" not in intent:
        greetings = {
            'hinglish': "Hello! Main aapki kaise help kar sakta hoon?",
            'hindi': "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?",
            'mixed': "Hi! Main aapki help ke liye ready hoon.",
            'english': "Hello! How can I assist you today?"
        }
        return {"role": "agent", "type": "info", "response": greetings.get(user_language, greetings['english'])}

    # 🚀 STEP 3: Detailed Question Handling (High Quality)
    if "QUESTION" in intent:
        answer_prompt = f"""{language_instruction}

You are an expert AI assistant for Quickfix, a comprehensive Customer Complaint Management platform.

USER QUESTION: {clean_msg}

YOUR TASK:
Provide a detailed, professional, and helpful answer that:
1. Directly and thoroughly addresses the user's question.
2. Explains relevant Quickfix features to show our value.
3. Uses a professional yet friendly tone.
4. Uses bullet points or numbered lists for steps.
5. Ends with an offer to help further.

KEY FEATURES YOU CAN EXPLAIN:
- AI Analysis: Automatic categorization and priority detection.
- Real-time Tracking: See exactly where your complaint is.
- Sentiment Analysis: We detect the emotion to prioritize urgent issues.
- Solution Suggestions: AI recommends instant fixes for common problems.
- 24/7 Availability: We're always here via this chatbot.
- Multi-language support: English, Hindi, Hinglish, etc.

CRITICAL: Respond COMPLETELY in the SAME language/style as the user's question.

ANSWER:"""
        
        try:
            answer = await asyncio.wait_for(async_ask_gemini(answer_prompt), timeout=15.0)
            return {"role": "agent", "type": "info", "response": answer}
        except Exception as e:
            print(f"Chatbot answer failed: {e}")
            return {"role": "agent", "type": "info", "response": "Sorry, I am having trouble answering right now. Please try again!"}

    # 🚀 STEP 4: Complaint Pipeline (Complex Processing)
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
