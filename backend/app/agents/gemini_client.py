import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=API_KEY)

# ✅ UPDATED MODEL NAME (Gemini 2.5 Flash is the current standard)
# You can also use "gemini-2.5-pro" if you need higher reasoning capabilities.
model = genai.GenerativeModel("gemini-2.5-flash") 

def ask_gemini(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()

        return "I couldn’t generate a response right now."

    except Exception as e:
        print("⚠ Gemini error:", e)
        return "AI service is temporarily unavailable."

# Test it
if __name__ == "__main__":
    print(ask_gemini("Hello, are you working?"))