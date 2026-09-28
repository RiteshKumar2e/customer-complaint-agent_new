import asyncio
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Optional

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

# Gemini retires model names regularly (gemini-2.0-flash now 404s), so the
# model is picked from what the API lists for this key. GEMINI_MODEL pins one.
GEMINI_MODEL_OVERRIDE = os.getenv("GEMINI_MODEL", "").strip()
# Verified 2026-09-28 with this account's key, fastest first. Pro models are
# left out (429 quota on this plan) and gemma returns multi-part responses.
PREFERRED_MODELS = [
    "gemini-flash-latest",     # ~4s, tracks Google's current flash
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
    "gemini-3.8-flash",        # works but ~15s
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
]
# Used if listing fails
FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash"]
_SKIP_MARKERS = ("image", "tts", "audio", "live", "embedding", "vision", "thinking", "exp", "preview", "robotics")

_gemini_models: Optional[List[str]] = None
_dead_models = set()


def rank_gemini_models(names: List[str]) -> List[str]:
    """Stable text models first, flash before pro/lite, newest version first."""
    def key(name):
        short = name.split("/")[-1]
        version = [float(v) for v in re.findall(r"gemini-(\d+(?:\.\d+)?)", short)]
        return (
            any(marker in short for marker in _SKIP_MARKERS),
            not ("flash" in short and "lite" not in short),
            -(version[0] if version else 0.0),
            short,
        )
    return [n.split("/")[-1] for n in sorted(names, key=key)]


def _list_gemini_models() -> List[str]:
    try:
        return [
            m.name for m in genai.list_models()
            if "generateContent" in getattr(m, "supported_generation_methods", [])
            and "gemini" in m.name
        ]
    except Exception as e:
        print(f"⚠️ Could not list Gemini models, using defaults: {e}")
        return []


async def gemini_models() -> List[str]:
    """Candidate models in order of preference, discovered once per process."""
    global _gemini_models
    if _gemini_models is None:
        listed = await asyncio.to_thread(_list_gemini_models)
        short_names = {n.split("/")[-1] for n in listed}
        # Known-good models the key still lists, then anything newer we haven't vetted
        preferred = [m for m in PREFERRED_MODELS if not listed or m in short_names]
        ordered = (
            ([GEMINI_MODEL_OVERRIDE] if GEMINI_MODEL_OVERRIDE else [])
            + preferred
            + [m for m in rank_gemini_models(listed) if "pro" not in m]
            + FALLBACK_MODELS
        )
        _gemini_models = list(dict.fromkeys(ordered))
        print(f"✅ Gemini model order: {', '.join(_gemini_models[:4])}")
    return [m for m in _gemini_models if m not in _dead_models]

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

def _is_model_gone(error_msg: str) -> bool:
    return any(s in error_msg for s in ("404", "not found", "no longer available", "not supported", "deprecated"))


async def _generate_with_any_model(prompt: str) -> Optional[str]:
    """Try the discovered models in order; retired ones are skipped for good."""
    for model_name in (await gemini_models())[:3]:
        try:
            response = await genai.GenerativeModel(model_name).generate_content_async(prompt)
            if response and response.text:
                print(f"✅ Gemini success with model: {model_name}")
                return response.text.strip()
        except Exception as e:
            msg = str(e).lower()
            if _is_model_gone(msg):
                print(f"⚠️ Gemini model {model_name} unavailable, trying next: {e}")
                _dead_models.add(model_name)
                continue
            raise  # quota / auth errors are handled per key by the caller
    return None


# Initialize Gemini with first available key
if API_KEYS:
    configure_current_key()

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
            
            text = await _generate_with_any_model(prompt)
            if text:
                return text

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