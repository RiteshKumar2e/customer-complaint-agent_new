import os
from dotenv import load_dotenv
from groq import Groq
from typing import Optional

load_dotenv()

class GroqClient:
    """
    Groq API Client - Ultra-fast LLM inference
    Primary AI service with automatic fallback to Gemini
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            print(f"✅ Groq API initialized with model: {self.model}")
        else:
            self.client = None
            print("⚠️ GROQ_API_KEY not set - Groq will be skipped")
    
    async def generate(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """
        Generate response using Groq API
        Returns None if Groq fails (triggers fallback to Gemini)
        """
        if not self.client:
            return None
        
        try:
            # Groq API call
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=max_tokens,
                top_p=1,
                stream=False,
            )
            
            response = chat_completion.choices[0].message.content
            
            if response and response.strip():
                return response.strip()
            
            return None
            
        except Exception as e:
            print(f"⚠️ Groq API error: {e}")
            return None

# Global instance
groq_client = GroqClient()
