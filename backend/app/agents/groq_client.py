import os
import re
from dotenv import load_dotenv
from groq import AsyncGroq
from typing import Optional, List

load_dotenv()

# Not usable for complaint handling: audio/voice, safety classifiers, and
# allam (answers in Arabic)
_NON_CHAT_MARKERS = ("whisper", "tts", "guard", "playai", "orpheus", "compound", "embed", "allam")
# Verified 2026-09-28 against this account's key (all return valid JSON mode
# output); anything else the API lists follows, largest first.
_PREFERRED = ("openai/gpt-oss-120b", "qwen/qwen3", "openai/gpt-oss-20b")


def is_chat_model(model_id: str) -> bool:
    lowered = model_id.lower()
    return not any(marker in lowered for marker in _NON_CHAT_MARKERS)


def _param_size(model_id: str) -> float:
    sizes = re.findall(r"(\d+(?:\.\d+)?)b\b", model_id.lower())
    return max((float(s) for s in sizes), default=0.0)


def rank_models(model_ids: List[str]) -> List[str]:
    """GROQ_MODELS (comma-separated) first, then known-good families, then by size."""
    pinned = [m.strip() for m in os.getenv("GROQ_MODELS", "").split(",") if m.strip()]

    def rank(model_id):
        for i, prefix in enumerate(_PREFERRED):
            if model_id.startswith(prefix):
                return (0, i, 0.0)
        return (1, 0, -_param_size(model_id))

    ordered = sorted(set(model_ids), key=lambda m: (rank(m), m))
    return [m for m in pinned if m in model_ids] + [m for m in ordered if m not in pinned]


class GroqClient:
    """
    Groq API Client with Multi-Model Fallback
    Automatically tries multiple models if one fails
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        
        # Used only if listing models fails; discover_models() normally
        # replaces this with what the key can actually use. Every model in the
        # old 29-entry list had been retired (400/404 in production).
        self.models: List[str] = [
            "openai/gpt-oss-120b",   # best quality, ~0.6s
            "qwen/qwen3.8-27b",      # fastest, ~0.2s
            "openai/gpt-oss-20b",
        ]

        # Cap how many models we try before giving up so a rate-limited or
        # degraded Groq endpoint fails over to Gemini/local quickly instead of
        # grinding through every model sequentially.
        self.max_fallback_attempts = 4
        
        # Track which models have failed
        self.failed_models = set()
        self.current_model_index = 0
        # The hardcoded list above goes stale as Groq retires models (every one
        # of them 400/404'd in production). On first use we ask the API which
        # models this key can actually use and rebuild the list from that.
        self._models_discovered = False
        self.live_models: Optional[List[str]] = None  # set only if discovery succeeded

        if self.api_key:
            # Async client with a hard per-request timeout and no internal retry
            # stacking (we handle model fallback ourselves). This keeps the event
            # loop unblocked so the caller's asyncio.wait_for timeouts work.
            self.client = AsyncGroq(api_key=self.api_key, timeout=8.0, max_retries=0)
            print(f"✅ Groq API initialized with {len(self.models)} fallback models")
            print(f"🎯 Primary model: {self.models[0]}")
        else:
            self.client = None
            print("⚠️ GROQ_API_KEY not set - Groq will be skipped")
    
    async def discover_models(self) -> List[str]:
        """Replace self.models with the chat models this API key can use (once)."""
        if self._models_discovered or not self.client:
            return self.models
        self._models_discovered = True
        try:
            listing = await self.client.models.list()
            available = [
                m.id for m in listing.data
                if getattr(m, "active", True) is not False and is_chat_model(m.id)
            ]
        except Exception as e:
            print(f"⚠️ Could not list Groq models, keeping built-in list: {e}")
            return self.models

        if available:
            self.models = rank_models(available)
            self.live_models = list(self.models)
            self.failed_models.clear()
            self.current_model_index = 0
            print(f"✅ Groq models available: {', '.join(self.models[:6])}"
                  f"{' …' if len(self.models) > 6 else ''}")
        return self.models

    def get_next_model(self) -> Optional[str]:
        """Get the next available model that hasn't failed"""
        attempts = 0
        while attempts < len(self.models):
            model = self.models[self.current_model_index]
            
            # If this model hasn't failed, use it
            if self.current_model_index not in self.failed_models:
                return model
            
            # Move to next model
            self.current_model_index = (self.current_model_index + 1) % len(self.models)
            attempts += 1
        
        # All models failed - reset and try again
        print("⚠️ All Groq models exhausted. Resetting...")
        self.failed_models.clear()
        self.current_model_index = 0
        return self.models[0] if self.models else None
    
    def mark_model_failed(self):
        """Mark current model as failed and move to next"""
        self.failed_models.add(self.current_model_index)
        print(f"❌ Groq model #{self.current_model_index + 1} ({self.models[self.current_model_index]}) failed")
        self.current_model_index = (self.current_model_index + 1) % len(self.models)
    
    async def generate(self, prompt: str, max_tokens: int = 2048) -> Optional[str]:
        """
        Generate response using Groq API with automatic model fallback
        Tries multiple models until one succeeds
        """
        if not self.client:
            return None

        await self.discover_models()
        max_attempts = min(len(self.models), self.max_fallback_attempts)

        for attempt in range(max_attempts):
            current_model = self.get_next_model()
            
            if not current_model:
                print("❌ No Groq models available")
                return None
            
            try:
                print(f"🚀 Trying Groq model: {current_model} (attempt {attempt + 1}/{max_attempts})")
                
                # Groq API call with optimized parameters (async — non-blocking)
                chat_completion = await self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert customer support specialist. Provide detailed, empathetic, and professional responses. Always be specific with timelines and action steps."
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=current_model,
                    temperature=0.8,  # Higher for more creative, human-like responses
                    max_tokens=max_tokens,
                    top_p=0.95,  # Slightly lower for more focused responses
                    frequency_penalty=0.2,  # Reduce repetition
                    presence_penalty=0.1,  # Encourage diverse vocabulary
                    stream=False,
                )
                
                response = chat_completion.choices[0].message.content
                
                if response and response.strip():
                    print(f"✅ Groq success with model: {current_model}")
                    return response.strip()
                
                # Empty response - try next model
                print(f"⚠️ Empty response from {current_model}, trying next model...")
                self.mark_model_failed()
                continue
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a model-specific error
                if "decommissioned" in error_msg or "not found" in error_msg or "invalid" in error_msg:
                    print(f"⚠️ Model {current_model} unavailable: {e}")
                    self.mark_model_failed()
                    
                    # Try next model
                    if attempt < max_attempts - 1:
                        continue
                
                # Check if it's a rate limit error
                elif "rate limit" in error_msg or "429" in error_msg:
                    print(f"⚠️ Rate limit hit on {current_model}")
                    self.mark_model_failed()
                    
                    # Try next model
                    if attempt < max_attempts - 1:
                        continue
                
                else:
                    print(f"⚠️ Groq error with {current_model}: {e}")
                    self.mark_model_failed()
                    
                    # Try next model
                    if attempt < max_attempts - 1:
                        continue
        
        print("❌ All Groq models failed")
        return None

# Global instance
groq_client = GroqClient()
