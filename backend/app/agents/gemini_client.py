import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Optional
import time

load_dotenv()

# ✅ Multi-API-Key Support with Automatic Rotation
# Configure multiple API keys separated by commas in .env file
# Example: GEMINI_API_KEY=key1,key2,key3,key4,key5
API_KEYS_STRING = os.getenv("GEMINI_API_KEY", "")
if not API_KEYS_STRING:
    raise RuntimeError("GEMINI_API_KEY not set")

# Parse multiple API keys (comma-separated)
API_KEYS: List[str] = [key.strip() for key in API_KEYS_STRING.split(",") if key.strip()]
if not API_KEYS:
    raise RuntimeError("No valid GEMINI_API_KEY found")

print(f"✅ Loaded {len(API_KEYS)} Gemini API key(s)")

# Track current key index and failed keys
current_key_index = 0
failed_keys = set()  # Track keys that have hit quota limits

# ✅ List of supported models for fallback
SUPPORTED_MODELS = [
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

def get_next_available_key() -> Optional[str]:
    """Get the next available API key that hasn't failed."""
    global current_key_index
    
    # Try all keys starting from current index
    attempts = 0
    while attempts < len(API_KEYS):
        key = API_KEYS[current_key_index]
        
        # If this key hasn't failed, use it
        if current_key_index not in failed_keys:
            print(f"🔑 Using API key #{current_key_index + 1}/{len(API_KEYS)}")
            return key
        
        # Move to next key
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        attempts += 1
    
    # All keys have failed - reset and try again
    print("⚠️ All API keys have been exhausted. Resetting and retrying...")
    failed_keys.clear()
    return API_KEYS[0] if API_KEYS else None

def mark_key_as_failed():
    """Mark the current API key as failed and rotate to next one."""
    global current_key_index
    
    failed_keys.add(current_key_index)
    print(f"❌ API key #{current_key_index + 1} has hit quota limit or failed")
    
    # Rotate to next key
    current_key_index = (current_key_index + 1) % len(API_KEYS)

def configure_current_key():
    """Configure genai with the current available API key."""
    key = get_next_available_key()
    if key:
        genai.configure(api_key=key)
        return True
    return False

def get_model():
    """Returns a generative model instance by trying multiple versions."""
    for model_name in SUPPORTED_MODELS:
        try:
            m = genai.GenerativeModel(model_name)
            return m
        except Exception:
            continue
    return genai.GenerativeModel("gemini-2.5-flash")  # Absolute fallback

# Initialize with first available key
configure_current_key()
model = get_model()

async def async_ask_gemini(prompt: str) -> str:
    """
    Asynchronous version of GEMINI request with automatic API key rotation.
    If quota is exceeded on one key, automatically tries the next available key.
    """
    max_key_attempts = len(API_KEYS)
    
    for attempt in range(max_key_attempts):
        try:
            # Ensure we're using a valid key
            if not configure_current_key():
                raise Exception("All API keys exhausted - triggering fallback")
            
            # Recreate model with current key
            current_model = get_model()
            
            # Try to generate content
            response = await current_model.generate_content_async(prompt)
            
            if response and response.text:
                return response.text.strip()
                
            # If no text in response, try next key
            if attempt < max_key_attempts - 1:
                continue
            else:
                raise Exception("No valid response from Gemini - triggering fallback")

        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a quota/rate limit error
            if "quota" in error_msg or "rate limit" in error_msg or "resource exhausted" in error_msg or "429" in error_msg:
                print(f"⚠️ Quota exceeded on attempt {attempt + 1}/{max_key_attempts}")
                mark_key_as_failed()
                
                # If we have more keys to try, continue to next iteration
                if attempt < max_key_attempts - 1:
                    print(f"🔄 Rotating to next API key...")
                    continue
            else:
                # For other errors, try fallback model once
                print(f"⚠ Async Gemini error: {e}")
                try:
                    fallback_m = genai.GenerativeModel("gemini-1.5-flash")
                    res = await fallback_m.generate_content_async(prompt)
                    if res and res.text:
                        return res.text.strip()
                except:
                    pass
            
            # If it's the last attempt, raise exception to trigger fallback
            if attempt == max_key_attempts - 1:
                print("❌ All Gemini attempts failed - triggering local LLM fallback")
                raise Exception("Gemini API unavailable - triggering fallback system")
    
    # This should never be reached, but just in case
    raise Exception("All API keys exhausted - triggering fallback system")

# Test it
if __name__ == "__main__":
    import asyncio
    print(asyncio.run(async_ask_gemini("Hello, are you working?")))