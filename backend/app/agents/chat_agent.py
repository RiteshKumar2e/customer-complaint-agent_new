from app.agents.gemini_client import async_ask_gemini
from app.agents.orchestrator import run_agent_pipeline
from app.agents.language_detector import detect_language, get_language_instruction, get_language_example
import sys
import os

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
    Async to handle high traffic and concurrent users.
    """
    msg_len = len(message.strip())
    if msg_len == 0:
        return {"role": "agent", "type": "info", "response": "How can I help you today?"}

    # 🌐 LANGUAGE DETECTION - Critical for multilingual support
    user_language = detect_language(message)
    language_instruction = get_language_instruction(user_language)
    
    print(f"🌐 Detected Language: {user_language}")

    # Intent detection with few-shot examples from training data
    intent_prompt = f"""
{CLASSIFICATION_EXAMPLES}

Classify the user message into ONE word: COMPLAINT or QUESTION.
Message: {message}

Rules:
- If user is reporting an issue, bug, or service failure, it's a COMPLAINT.
- If user is asking HOW the site works or general info, it's a QUESTION.
- If query is very short (e.g., "Hi", "Hello", "test"), it's a QUESTION.

Only return ONE word.
"""
    try:
        intent_res = await async_ask_gemini(intent_prompt)
        intent = intent_res.upper()
    except:
        intent = "QUESTION"

    # Short query handling
    if msg_len < 10 and "COMPLAINT" not in intent:
        # Return greeting in user's language
        greetings = {
            'hinglish': "Hello! Main aapki kaise help kar sakta hoon?",
            'hindi': "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?",
            'mixed': "Hi! Main aapki help ke liye ready hoon.",
            'english': "Hello! How can I assist you today?"
        }
        return {"role": "agent", "type": "info", "response": greetings.get(user_language, greetings['english'])}

    if "QUESTION" in intent:
        # Enhanced prompt for detailed, helpful answers IN USER'S LANGUAGE
        if msg_len < 30:
            # Short questions - concise but complete answers
            answer_prompt = f"""{language_instruction}

You are a helpful AI assistant for Quickfix, a Customer Complaint Management platform.

USER QUESTION: {message}

Provide a brief but complete answer (1-2 sentences). Be friendly and helpful.
IMPORTANT: Respond in the SAME language/style as the user's question above.

ANSWER:"""
        else:
            # Detailed questions - comprehensive answers
            answer_prompt = f"""{language_instruction}

You are an expert AI assistant for Quickfix, a comprehensive Customer Complaint Management platform.

USER QUESTION: {message}

YOUR TASK:
Provide a detailed, professional answer that:
1. Directly addresses the user's question
2. Provides specific steps or information (if applicable)
3. Uses clear, simple language
4. Includes examples when helpful
5. Ends with an offer to help further

PLATFORM FEATURES YOU CAN EXPLAIN:
- Complaint submission and tracking
- AI-powered complaint analysis and categorization
- Priority detection (High/Medium/Low)
- Sentiment analysis
- Automated solution suggestions
- Email notifications to users and admins
- Dashboard for viewing all complaints
- Real-time status updates
- Multi-language support
- 24/7 AI assistance

RESPONSE GUIDELINES:
- Be specific and actionable
- Use numbered steps for processes
- Mention relevant features
- Keep it professional but friendly
- Length: 2-4 sentences for simple questions, more for complex ones

CRITICAL: Respond in the SAME language/style as the user's question.

Language Example for {user_language}:
{get_language_example(user_language, 'question')}

Now provide a similarly detailed and helpful answer for the user's question above.

ANSWER:"""
        
        try:
            answer = await async_ask_gemini(answer_prompt)
            return {"role": "agent", "type": "info", "response": answer}
        except Exception as e:
            print(f"Chatbot answer generation failed: {e}")
            # Fallback response in user's language
            fallbacks = {
                'hinglish': "Main aapki help karna chahta hoon! Kya aap apna question dobara puch sakte hain?",
                'hindi': "मैं आपकी मदद करना चाहता हूँ! क्या आप अपना प्रश्न दोबारा पूछ सकते हैं?",
                'mixed': "I'm here to help! Kya aap apna question phir se puch sakte hain?",
                'english': "I'm here to help! Could you please rephrase your question or ask about our complaint management features, submission process, or tracking system?"
            }
            return {
                "role": "agent", 
                "type": "info", 
                "response": fallbacks.get(user_language, fallbacks['english'])
            }

    # If it's a complaint, run the full pipeline with language context
    result = await run_agent_pipeline(message, user_language=user_language)
    
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
