import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Optional
import time

# Import Groq client
try:
    from app.agents.groq_client import groq_client
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ Groq client not available")

load_dotenv()

# ✅ Multi-API-Key Support with Automatic Rotation (Gemini)
API_KEYS_STRING = os.getenv("GEMINI_API_KEY", "")
if not API_KEYS_STRING:
    print("⚠️ GEMINI_API_KEY not set - will rely on Groq only")
    API_KEYS = []
else:
    API_KEYS: List[str] = [key.strip() for key in API_KEYS_STRING.split(",") if key.strip()]
    print(f"✅ Loaded {len(API_KEYS)} Gemini API key(s)")

# Track current key index and failed keys
current_key_index = 0
failed_keys = set()

# ✅ List of supported Gemini models for fallback
SUPPORTED_MODELS = [
    "gemini-2.0-flash",
    "gemini-exp-1206",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemma-3-27b-it",
]

def get_next_available_key() -> Optional[str]:
    """Get the next available Gemini API key that hasn't failed."""
    global current_key_index
    
    if not API_KEYS:
        return None
    
    attempts = 0
    while attempts < len(API_KEYS):
        key = API_KEYS[current_key_index]
        
        if current_key_index not in failed_keys:
            print(f"🔑 Using Gemini API key #{current_key_index + 1}/{len(API_KEYS)}")
            return key
        
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        attempts += 1
    
    print("⚠️ All Gemini API keys exhausted. Resetting...")
    failed_keys.clear()
    return API_KEYS[0] if API_KEYS else None

def mark_key_as_failed():
    """Mark the current Gemini API key as failed and rotate to next one."""
    global current_key_index
    
    failed_keys.add(current_key_index)
    print(f"❌ Gemini API key #{current_key_index + 1} failed")
    current_key_index = (current_key_index + 1) % len(API_KEYS) if API_KEYS else 0

def configure_current_key():
    """Configure genai with the current available Gemini API key."""
    key = get_next_available_key()
    if key:
        genai.configure(api_key=key)
        return True
    return False

def get_model():
    """Returns a Gemini generative model instance by trying multiple versions."""
    for model_name in SUPPORTED_MODELS:
        try:
            m = genai.GenerativeModel(model_name)
            return m
        except Exception:
            continue
    return genai.GenerativeModel("gemini-2.5-flash")  # Absolute fallback

# Initialize Gemini with first available key
if API_KEYS:
    configure_current_key()
    model = get_model()
else:
    model = None

async def async_ask_ai(prompt: str) -> str:
    """
    Multi-tier AI request with automatic fallback:
    1. Try Groq (fastest, free tier)
    2. Try Gemini with key rotation
    3. Raise exception to trigger local LLM fallback
    """
    
    # ========================================
    # TIER 1: GROQ API (Primary - Ultra Fast)
    # ========================================
    if GROQ_AVAILABLE:
        try:
            print("🚀 Trying Groq API (Primary)...")
            groq_response = await groq_client.generate(prompt)
            if groq_response:
                print("✅ Groq API success!")
                return groq_response
            print("⚠️ Groq returned empty response, trying Gemini...")
        except Exception as e:
            print(f"⚠️ Groq API failed: {e}, falling back to Gemini...")
    
    # ========================================
    # TIER 2: GEMINI API (Fallback)
    # ========================================
    if not API_KEYS:
        print("❌ No Gemini keys available - triggering local fallback")
        raise Exception("Both Groq and Gemini unavailable - triggering fallback")
    
    max_key_attempts = len(API_KEYS)
    
    for attempt in range(max_key_attempts):
        try:
            print(f"🔄 Trying Gemini API (attempt {attempt + 1}/{max_key_attempts})...")
            
            if not configure_current_key():
                raise Exception("All Gemini keys exhausted - triggering fallback")
            
            current_model = get_model()
            response = await current_model.generate_content_async(prompt)
            
            if response and response.text:
                print("✅ Gemini API success!")
                return response.text.strip()
            
            if attempt < max_key_attempts - 1:
                continue
            else:
                raise Exception("No valid Gemini response - triggering fallback")

        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a quota/rate limit error
            if "quota" in error_msg or "rate limit" in error_msg or "resource exhausted" in error_msg or "429" in error_msg:
                print(f"⚠️ Gemini quota exceeded on attempt {attempt + 1}/{max_key_attempts}")
                mark_key_as_failed()
                
                if attempt < max_key_attempts - 1:
                    print(f"🔄 Rotating to next Gemini key...")
                    continue
            else:
                print(f"⚠️ Gemini error: {e}")
                # Try fallback Gemini model once
                try:
                    fallback_m = genai.GenerativeModel("gemini-1.5-flash")
                    res = await fallback_m.generate_content_async(prompt)
                    if res and res.text:
                        return res.text.strip()
                except:
                    pass
            
            # Last attempt - trigger local fallback
            if attempt == max_key_attempts - 1:
                print("❌ All Gemini attempts failed - triggering local LLM fallback")
                raise Exception("Gemini API unavailable - triggering fallback system")
    
    raise Exception("All AI APIs exhausted - triggering fallback system")

# Backward compatibility alias
async_ask_gemini = async_ask_ai

# Test
if __name__ == "__main__":
    import asyncio
    print(asyncio.run(async_ask_ai("Hello, are you working?")))