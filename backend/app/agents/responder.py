import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

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

# Category-specific professional fallback responses
CATEGORY_RESPONSES = {
    "Billing": "Thank you for contacting us about your billing concern. We understand how important accurate billing is, and we're reviewing your account details right away. Our billing team will reach out to you within 24-48 hours with a resolution.",
    "Technical": "We appreciate you reporting this technical issue. Our technical team is investigating this matter with high priority. We'll work to provide you with a fix or workaround within 24 hours and keep you updated throughout the process.",
    "Delivery": "We sincerely apologize for any delay with your delivery. We're actively tracking your order and will prioritize its delivery. You can expect an update from our logistics team within 12 hours.",
    "Service": "Thank you for bringing this service matter to our attention. We're sorry for any inconvenience you've experienced. Our customer service team will personally reach out to you within 24 hours to ensure this is resolved to your satisfaction.",
    "Security": "Your security and privacy are our top priorities. We're taking your concern very seriously and our security team is investigating immediately. You'll receive a detailed update within 6 hours.",
    "Other": "Thank you for contacting us. We've received your message and our support team is reviewing your case carefully. We'll respond with a solution within 24 hours."
}

async def generate_response(category: str, text: str) -> str:
    if not text or not text.strip():
        return "Thank you for reaching out. We are here to help."
    
    # Layer 1: Try AI (Groq/Gemini - Best quality, contextual)
    if model is not None:
        prompt = f"""You are a senior customer support specialist with exceptional communication skills.

COMPLAINT CATEGORY: {category}
CUSTOMER COMPLAINT: {text}

YOUR TASK:
Write a professional, empathetic response that:
1. Acknowledges the customer's specific issue and validates their feelings
2. Takes ownership and apologizes sincerely (if applicable)
3. Reassures them that action is being taken
4. Maintains a warm, professional tone

RESPONSE GUIDELINES:
- Address the specific issue mentioned (don't be generic)
- Show genuine empathy and understanding
- Use phrases like "I understand", "I sincerely apologize", "Let me help you"
- Be personal and human (avoid robotic language)
- Keep it concise but meaningful (2-4 sentences)
- End with reassurance or next steps

EXAMPLE QUALITY RESPONSES:

For Billing Complaint:
"I sincerely apologize for the billing error you've experienced - I completely understand how frustrating it is to see unexpected charges on your account. I've immediately flagged your case for our senior billing team, and they'll audit your account within the next 4 hours to identify and correct any discrepancies. You have my commitment that we'll resolve this swiftly and ensure it doesn't happen again."

For Technical Issue:
"I understand how disruptive technical issues can be, especially when you're trying to get work done. I've escalated your case to our Level 2 technical team who specialize in this exact issue, and they're already investigating the root cause. You'll receive an update within 2 hours with either a permanent fix or a reliable workaround, and I'll personally monitor this until it's fully resolved."

For Delivery Delay:
"I'm truly sorry for the delay in your delivery - I know how disappointing it is when a package doesn't arrive as expected. I've personally contacted our logistics partner and your order is now flagged for priority handling, with an expected delivery within 24-48 hours. As a gesture of goodwill for this inconvenience, I'm also upgrading your next delivery to express shipping at no charge."

Now write a similarly empathetic, specific, and professional response for the {category} complaint above.

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
    
    # Layer 4: Category-specific professional fallback (Always works)
    return CATEGORY_RESPONSES.get(category, CATEGORY_RESPONSES["Other"])

