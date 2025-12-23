import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=API_KEY)

# 🚀 SYSTEM INSTRUCTIONS: The "Brain" of the Agent
# This ensures the model adapts its response length to the user's input complexity.
SYSTEM_INSTRUCTION = """
You are the "Quickfix Support AI", a highly intelligent and adaptive virtual assistant for the Quickfix Customer Complaint Platform.

### YOUR RULES:
1. **Adaptive Length**: 
   - If the user provides a short or simple prompt (e.g., "Hi", "Hello", "How are you?"), respond with a VERY simple, warm, and professional one-line greeting. Do NOT be verbose.
   - If the user asks a complex question, provides a detailed complaint, or needs technical help, provide a thorough, structured, and professional "proper" answer. Use bullet points or sections if needed.
2. **Persona**: You are empathetic, professional, and solution-oriented.
3. **Context**: You are part of the Quickfix application, where users submit complaints and AI analyzes them. Your goal is to make the user feel heard and supported.
4. **No Fluff**: Get straight to the point. If it's a greeting, just greet. If it's a problem, solve it.
"""

# 💎 Using Gemini 1.5 Flash for the perfect balance of speed and intelligence
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

def ask_gemini(prompt: str) -> str:
    """
    Asks Gemini a question. The model will automatically follow the 
    system instructions to provide simple or detailed answers.
    """
    try:
        # Configuration for better control
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 1024,
        }

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        if response and response.text:
            return response.text.strip()

        return "I'm here to help, but I couldn't process that specific request. Could you rephrase it?"

    except Exception as e:
        print(f"⚠️ Gemini Assistant Error: {str(e)}")
        return "Our AI service is currently taking a short break. Please try again in a moment!"

# 🧪 Quick Test (When run directly)
if __name__ == "__main__":
    print("\n--- Testing Simple Prompt ---")
    print(f"User: Hi | AI: {ask_gemini('Hi')}")
    
    print("\n--- Testing Complex Prompt ---")
    print(f"User: How does Quickfix handle my security? | AI: {ask_gemini('How does Quickfix handle my security and data privacy?')}\n")