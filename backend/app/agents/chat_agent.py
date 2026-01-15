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

# Quick response templates for common queries
QUICK_RESPONSES = {
    'english': {
        'greetings': ["hi", "hello", "hey", "namaste", "hola"],
        'thanks': ["thank", "thanks", "thankyou", "dhanyavaad"],
        'help': ["help", "assist", "support"],
        'responses': {
            'greeting': "Hello! 👋 I'm your AI assistant. I can help you with:\n• Submitting and tracking complaints\n• Understanding our platform features\n• Getting instant support\n\nHow can I help you today?",
            'thanks': "You're welcome! 😊 Feel free to ask if you need anything else.",
            'help': "I'm here to help! You can:\n• Report a complaint or issue\n• Ask about platform features\n• Track your complaint status\n• Get instant solutions\n\nWhat would you like to know?"
        }
    },
    'hinglish': {
        'greetings': ["hi", "hello", "hey", "namaste", "hola"],
        'thanks': ["thank", "thanks", "thankyou", "dhanyavaad", "shukriya"],
        'help': ["help", "assist", "support", "madad"],
        'responses': {
            'greeting': "Hello! 👋 Main aapka AI assistant hoon. Main aapki help kar sakta hoon:\n• Complaints submit aur track karne mein\n• Platform features samajhne mein\n• Instant support dene mein\n\nAaj main aapki kaise madad kar sakta hoon?",
            'thanks': "Aapka swagat hai! 😊 Agar kuch aur chahiye toh zaroor batayein.",
            'help': "Main yahan help karne ke liye hoon! Aap:\n• Complaint ya issue report kar sakte hain\n• Platform features ke baare mein pooch sakte hain\n• Apni complaint ka status track kar sakte hain\n• Instant solutions le sakte hain\n\nAap kya jaanna chahte hain?"
        }
    }
}

def get_quick_response(message: str, language: str = 'english') -> str:
    """Check if message matches quick response patterns"""
    msg_lower = message.lower().strip()
    templates = QUICK_RESPONSES.get(language, QUICK_RESPONSES['english'])
    
    # Check greetings
    if any(greet in msg_lower for greet in templates['greetings']):
        return templates['responses']['greeting']
    
    # Check thanks
    if any(thank in msg_lower for thank in templates['thanks']):
        return templates['responses']['thanks']
    
    # Check help requests
    if any(help_word in msg_lower for help_word in templates['help']):
        return templates['responses']['help']
    
    return None

async def handle_chat_message(message: str) -> dict:
    """
    Optimized chat handler with instant responses for common queries.
    Detects user's language and responds in the SAME language.
    Async with timeout to handle high traffic.
    """
    msg_len = len(message.strip())
    if msg_len == 0:
        return {"role": "agent", "type": "info", "response": "How can I help you today?"}

    # 🌐 LANGUAGE DETECTION - Critical for multilingual support
    user_language = detect_language(message)
    print(f"🌐 Detected Language: {user_language}")

    # ⚡ INSTANT RESPONSE for common queries (no AI call needed)
    quick_resp = get_quick_response(message, user_language)
    if quick_resp:
        print("⚡ Quick response matched - instant reply!")
        return {"role": "agent", "type": "info", "response": quick_resp}

    # Short query handling (greetings, etc.)
    if msg_len < 10:
        greetings = {
            'hinglish': "Hello! Main aapki kaise help kar sakta hoon?",
            'hindi': "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?",
            'mixed': "Hi! Main aapki help ke liye ready hoon.",
            'english': "Hello! How can I assist you today?"
        }
        return {"role": "agent", "type": "info", "response": greetings.get(user_language, greetings['english'])}

    # ⚡ FAST INTENT DETECTION (simplified prompt for speed)
    intent_prompt = f"""Classify in ONE word: COMPLAINT or QUESTION

Message: {message}

COMPLAINT = reporting issue/problem/bug
QUESTION = asking how something works

Answer:"""
    
    try:
        # Add 10-second timeout for intent detection
        intent_res = await asyncio.wait_for(
            async_ask_gemini(intent_prompt),
            timeout=10.0
        )
        intent = intent_res.upper()
        print(f"🎯 Intent detected: {intent}")
    except asyncio.TimeoutError:
        print("⏱️ Intent detection timeout - defaulting to QUESTION")
        intent = "QUESTION"
    except Exception as e:
        print(f"⚠️ Intent detection failed: {e} - defaulting to QUESTION")
        intent = "QUESTION"

    # QUESTION HANDLING - Optimized for speed
    if "QUESTION" in intent:
        language_instruction = get_language_instruction(user_language)
        
        # Simplified prompt for faster response
        answer_prompt = f"""{language_instruction}

You are a helpful AI assistant for Quickfix Customer Complaint Platform.

USER QUESTION: {message}

Provide a clear, helpful answer (2-3 sentences max).
Respond in the SAME language as the question.

ANSWER:"""
        
        try:
            # Add 10-second timeout for answer generation
            answer = await asyncio.wait_for(
                async_ask_gemini(answer_prompt),
                timeout=10.0
            )
            print("✅ Answer generated successfully")
            return {"role": "agent", "type": "info", "response": answer}
        except asyncio.TimeoutError:
            print("⏱️ Answer generation timeout")
            fallbacks = {
                'hinglish': "Sorry, response mein delay ho raha hai. Kya aap apna question dobara puch sakte hain?",
                'hindi': "क्षमा करें, उत्तर में देरी हो रही है। क्या आप अपना प्रश्न दोबारा पूछ सकते हैं?",
                'mixed': "Sorry for the delay. Kya aap apna question phir se puch sakte hain?",
                'english': "I apologize for the delay. Could you please rephrase your question?"
            }
            return {
                "role": "agent", 
                "type": "info", 
                "response": fallbacks.get(user_language, fallbacks['english'])
            }
        except Exception as e:
            print(f"❌ Answer generation failed: {e}")
            fallbacks = {
                'hinglish': "Main aapki help karna chahta hoon! Kya aap apna question dobara puch sakte hain?",
                'hindi': "मैं आपकी मदद करना चाहता हूँ! क्या आप अपना प्रश्न दोबारा पूछ सकते हैं?",
                'mixed': "I'm here to help! Kya aap apna question phir se puch sakte hain?",
                'english': "I'm here to help! Could you please rephrase your question?"
            }
            return {
                "role": "agent", 
                "type": "info", 
                "response": fallbacks.get(user_language, fallbacks['english'])
            }

    # COMPLAINT HANDLING - Run full pipeline with timeout
    try:
        print("🔄 Running complaint pipeline...")
        # Add 15-second timeout for full pipeline
        result = await asyncio.wait_for(
            run_agent_pipeline(message, user_language=user_language),
            timeout=15.0
        )
        
        # Check if we have a template for this category/priority
        category = result["category"]
        priority = result["priority"]
        templated_response = RESPONSE_TEMPLATES.get(category, {}).get(priority)
        
        # If templated response exists and message is short, use it
        final_response = templated_response if (templated_response and msg_len < 50) else result["response"]

        print("✅ Complaint processed successfully")
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
