import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=API_KEY)

# ✅ List of supported models for fallback
# We try these in order and use the first one that works.
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

def get_model():
    """Returns a generative model instance by trying multiple versions."""
    for model_name in SUPPORTED_MODELS:
        try:
            m = genai.GenerativeModel(model_name)
            # Minimal check to see if the model name is accepted
            return m
        except Exception:
            continue
    return genai.GenerativeModel("gemini-2.5-flash") # Absolute fallback

model = get_model()

async def async_ask_gemini(prompt: str) -> str:
    """Asynchronous version of GEMINI request for high performance scaling."""
    try:
        response = await model.generate_content_async(prompt)
        
        if response and response.text:
            return response.text.strip()
            
        return "I couldn’t generate a response right now."

    except Exception as e:
        print(f"⚠ Async Gemini error with {model.model_name}:", e)
        try:
            # Fallback for speed
            fallback_m = genai.GenerativeModel("gemini-1.5-flash")
            res = await fallback_m.generate_content_async(prompt)
            if res and res.text:
                return res.text.strip()
        except:
            pass
        return "AI service is temporarily unavailable."

# Test it
if __name__ == "__main__":
    print(ask_gemini("Hello, are you working?"))