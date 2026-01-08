import sys
import os
from app.agents.gemini_client import async_ask_gemini

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

# Category-specific fallback solutions
CATEGORY_SOLUTIONS = {
    "Billing": "We will review your billing details and process any necessary refunds within 24-48 hours. Our billing team will contact you with a resolution.",
    "Technical": "Our technical team will investigate this issue immediately. We'll provide a fix or workaround within 24 hours and keep you updated.",
    "Delivery": "We apologize for the delay. We're tracking your order and will ensure priority delivery. You'll receive an update within 12 hours.",
    "Service": "We're sorry for the inconvenience. Our service team will reach out to you within 24 hours to resolve this matter personally.",
    "Security": "Your security is our priority. Our security team is investigating this immediately and will contact you within 6 hours with an update.",
    "Other": "Thank you for bringing this to our attention. Our support team will review your case and respond with a solution within 24 hours."
}

async def suggest_solution(category: str, text: str) -> str:
    if not text or not text.strip():
        return "Please contact our support team for assistance."

    # Enhanced prompt for high-quality solutions
    prompt = f"""You are an expert customer service solution specialist with 10+ years of experience.

COMPLAINT CATEGORY: {category}
CUSTOMER ISSUE: {text}

YOUR TASK:
Provide a comprehensive, professional solution that:
1. Acknowledges the specific problem
2. Provides concrete action steps with timelines
3. Shows empathy and understanding
4. Gives specific details (not generic responses)
5. Includes what the customer can expect next

SOLUTION FORMAT:
- Start with acknowledgment of the issue
- Provide 2-3 specific action steps
- Include realistic timelines (hours/days)
- End with reassurance

EXAMPLE QUALITY SOLUTIONS:

For Billing Issues:
"I sincerely apologize for the billing discrepancy you've encountered. Here's how we'll resolve this immediately: (1) I'm escalating your case to our senior billing specialist who will audit your account within the next 4 hours. (2) Any duplicate charges will be refunded to your original payment method within 3-5 business days. (3) You'll receive a detailed breakdown via email showing the corrections made. We'll also add a $10 courtesy credit to your account for the inconvenience."

For Technical Issues:
"I understand how frustrating technical issues can be, especially when they impact your work. Here's our resolution plan: (1) Our Level 2 technical team will investigate your specific error code within the next 2 hours. (2) We'll provide either a permanent fix or a temporary workaround by end of day. (3) I'm assigning you a dedicated support ticket number and you'll receive hourly updates via email until this is fully resolved."

For Delivery Issues:
"I apologize for the delay in your delivery. Let me take immediate action: (1) I've contacted our logistics partner and your package is now flagged for priority delivery. (2) Based on current tracking, you should receive it within 24-48 hours. (3) I'm applying a 20% discount to your next order and upgrading your delivery to express shipping at no cost. You'll receive SMS updates every 6 hours until delivery is confirmed."

Now provide a similarly detailed, specific, and professional solution for the customer's {category} complaint above.

IMPORTANT: 
- Be specific with timelines (e.g., "within 4 hours", "by tomorrow", "3-5 business days")
- Mention specific teams/departments that will help
- Include compensation/goodwill gestures when appropriate
- Use empathetic language
- Keep it professional but warm
- Length: 3-5 sentences with concrete details

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
    
    # Layer 3: Category-specific fallback (Always works)
    return CATEGORY_SOLUTIONS.get(category, CATEGORY_SOLUTIONS["Other"])
