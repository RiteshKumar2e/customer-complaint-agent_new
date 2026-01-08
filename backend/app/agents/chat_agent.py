from app.agents.gemini_client import async_ask_gemini
from app.agents.orchestrator import run_agent_pipeline
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
    Async to handle high traffic and concurrent users.
    """
    msg_len = len(message.strip())
    if msg_len == 0:
        return {"role": "agent", "type": "info", "response": "How can I help you today?"}

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
        return {"role": "agent", "type": "info", "response": "Hello! How can I assist you today?"}

    if "QUESTION" in intent:
        # Enhanced prompt for detailed, helpful answers
        if msg_len < 30:
            # Short questions - concise but complete answers
            answer_prompt = f"""You are a helpful AI assistant for Quickfix, a Customer Complaint Management platform.

USER QUESTION: {message}

Provide a brief but complete answer (1-2 sentences). Be friendly and helpful.

ANSWER:"""
        else:
            # Detailed questions - comprehensive answers
            answer_prompt = f"""You are an expert AI assistant for Quickfix, a comprehensive Customer Complaint Management platform.

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

EXAMPLE QUALITY ANSWERS:

Question: "How do I submit a complaint?"
Answer: "Submitting a complaint is easy! Simply click the 'Submit Complaint' button on the dashboard, fill in the subject and description of your issue, and click submit. Our AI will instantly analyze your complaint, categorize it, detect the priority level, and send you a confirmation email with a unique ticket ID. You'll receive updates as we work on resolving your issue."

Question: "How long does it take to get a response?"
Answer: "Response times vary based on priority: High-priority issues (like billing errors or security concerns) are escalated immediately and typically receive a response within 2-4 hours. Medium-priority issues are addressed within 24 hours, while low-priority requests are handled within 48 hours. You'll receive email updates at each stage, and you can track your complaint status in real-time through your dashboard."

Question: "What is AI analysis?"
Answer: "Our AI analysis system automatically processes your complaint through multiple layers: (1) It categorizes your issue (Billing, Technical, Delivery, etc.), (2) Detects the priority level based on urgency and impact, (3) Analyzes the sentiment to understand your emotional state, and (4) Suggests potential solutions based on similar past cases. This entire process happens in seconds, ensuring you get immediate acknowledgment and faster resolution."

Now provide a similarly detailed and helpful answer for the user's question above.

ANSWER:"""
        
        try:
            answer = await async_ask_gemini(answer_prompt)
            return {"role": "agent", "type": "info", "response": answer}
        except Exception as e:
            print(f"Chatbot answer generation failed: {e}")
            # Fallback response
            return {
                "role": "agent", 
                "type": "info", 
                "response": "I'm here to help! Could you please rephrase your question or ask about our complaint management features, submission process, or tracking system?"
            }

    # If it's a complaint, run the full pipeline
    result = await run_agent_pipeline(message)
    
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
        "steps": result.get("steps", [])
    }
