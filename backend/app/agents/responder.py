import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    SUPPORTED_MODELS = [
       "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-exp-1206",
        "gemini-2.0-flash-lite",
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemma-3-27b-it",
        "gemini-3-flash-preview",
        "gemini-robotics-er-1.5-preview",
        "deep-research-pro-preview-12-2025"
    ]
    
    def initialize_best_model():
        for m_name in SUPPORTED_MODELS:
            try:
                return genai.GenerativeModel(m_name)
            except:
                continue
        return genai.GenerativeModel("gemini-2.5-flash")
    model = initialize_best_model()
else:
    model = None

def fallback_response(category: str) -> str:
    responses = {
        "Billing": "We understand your concern regarding billing. Our team is reviewing your issue and will assist you shortly.",
        "Technical": "Thank you for reporting this technical issue. Our engineers are actively working on a fix.",
        "Delivery": "We apologize for the delivery delay. Please be assured we are tracking this closely.",
        "Service": "We’re sorry for the inconvenience. Your feedback has been shared with our support team.",
        "Security": "Your security concern is important to us. Our security team is investigating this matter.",
        "Other": "Thank you for reaching out. We’ll get back to you as soon as possible."
    }
    return responses.get(category, responses["Other"])

async def generate_response(category: str, text: str) -> str:
    if not text or not text.strip():
        return fallback_response(category)
    if model is None:
        return fallback_response(category)
    prompt = f"""You are a professional customer support assistant.
Complaint: {text}
Category: {category}
Write a polite, professional, and reassuring response in 2–3 sentences."""
    try:
        response = await model.generate_content_async(prompt)
        if not response or not response.text:
            return fallback_response(category)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini generation error: {e}")
        return fallback_response(category)