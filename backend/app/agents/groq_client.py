import os
from dotenv import load_dotenv
from groq import Groq
from typing import Optional, List

load_dotenv()

class GroqClient:
    """
    Groq API Client with Multi-Model Fallback
    Automatically tries multiple models if one fails
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        
        # List of available Groq models (in order of preference)
        self.models: List[str] = [
            "llama-3.3-70b-versatile",      # Best quality, versatile
            "llama-3.1-70b-versatile",      # High quality, reliable
            "llama-3.2-90b-text-preview",   # Very high quality
            "llama-3.1-8b-instant",         # Fastest, good quality
            "mixtral-8x7b-32768",           # Good for complex tasks (if available)
            "gemma2-9b-it",                 # Fast, efficient
            "llama3-70b-8192",              # Reliable fallback
            "llama3-8b-8192",               # Fast fallback
            "gemma-7b-it",                  # Lightweight fallback
            "llama-3.2-3b-preview",         # Ultra-fast fallback
        ]
        
        # Track which models have failed
        self.failed_models = set()
        self.current_model_index = 0
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            print(f"✅ Groq API initialized with {len(self.models)} fallback models")
            print(f"🎯 Primary model: {self.models[0]}")
        else:
            self.client = None
            print("⚠️ GROQ_API_KEY not set - Groq will be skipped")
    
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
        
        max_attempts = len(self.models)
        
        for attempt in range(max_attempts):
            current_model = self.get_next_model()
            
            if not current_model:
                print("❌ No Groq models available")
                return None
            
            try:
                print(f"🚀 Trying Groq model: {current_model} (attempt {attempt + 1}/{max_attempts})")
                
                # Groq API call with optimized parameters
                chat_completion = self.client.chat.completions.create(
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
