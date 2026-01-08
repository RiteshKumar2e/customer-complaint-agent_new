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
        "gemini-2.0-flash-exp",
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
        return genai.GenerativeModel("gemini-2.5-flash")
    model = initialize_best_model()
else:
    model = None

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import RESPONSE_TEMPLATES
except ImportError:
    RESPONSE_TEMPLATES = {}

async def generate_response(category: str, text: str) -> str:
    if not text or not text.strip():
        return "Thank you for reaching out. We are here to help."
    
    # Try Gemini first
    if model is not None:
        prompt = f"""You are a professional customer support assistant.
Complaint: {text}
Category: {category}
Write a polite, professional, and reassuring response in 2–3 sentences."""
        try:
            response = await model.generate_content_async(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Gemini generation error: {e}")
    
    # Fallback to Local GPT-2 (No API quota, unlimited usage)
    if LOCAL_LLM_AVAILABLE:
        try:
            local_response = generate_local_response(
                f"Customer complaint about {category}: {text[:200]}"
            )
            if local_response and len(local_response) > 20:
                return local_response
        except:
            pass
    
    # Final fallback to templates
    return RESPONSE_TEMPLATES.get(category, {}).get("Medium", "We have received your complaint and are looking into it.")
