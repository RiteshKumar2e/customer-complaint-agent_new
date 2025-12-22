import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# -------------------------------
# Gemini Configuration
# -------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        # ✅ FIX: Updated to 'gemini-2.5-pro' (Current stable version)
        # 'gemini-pro' (1.0) is deprecated and causes the 404 error
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        print(f"Error initializing Gemini: {e}") # Optional: Print error for debugging
        model = None
else:
    model = None


# -------------------------------
# Fallback Responder
# -------------------------------
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


# -------------------------------
# Main Responder
# -------------------------------
def generate_response(category: str, text: str) -> str:
    """
    Generates a user-facing response for the complaint.
    """

    if not text or not text.strip():
        return fallback_response(category)

    # 🚨 Gemini unavailable → fallback
    if model is None:
        return fallback_response(category)

    prompt = f"""
You are a professional customer support assistant.

Complaint:
{text}

Category:
{category}

Write a polite, professional, and reassuring response in 2–3 sentences.
"""

    try:
        response = model.generate_content(prompt)

        if not response or not response.text:
            return fallback_response(category)

        return response.text.strip()

    except Exception as e:
        # 🔥 Gemini failure → fallback instead of 500 error
        print(f"Gemini generation error: {e}") # Helpful for debugging logs
        return fallback_response(category)