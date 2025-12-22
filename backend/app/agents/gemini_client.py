import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=API_KEY)

# Initialize model with generation config for better control
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 200,  # Keeps responses short
}

model = genai.GenerativeModel(
    "gemini-2.0-flash-exp",
    generation_config=generation_config
)

# System instruction for proper behavior
SYSTEM_PROMPT = """You are a helpful assistant. Follow these rules:
1. Give SHORT, DIRECT answers (2-3 sentences max)
2. Only provide what was asked - don't add extra information unless requested
3. For follow-up questions, answer them naturally without repeating previous context
4. Be conversational and friendly
5. If asked for details or elaboration, then provide more information
"""

# Chat history to maintain context
chat_history = []

def ask_gemini(prompt: str, use_history: bool = True) -> str:
    """
    Ask Gemini a question with proper training for short answers.
    
    Args:
        prompt: User's question
        use_history: Whether to use chat history for context
    
    Returns:
        AI response
    """
    try:
        # Build the full prompt with system instruction
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}\nAssistant:"
        
        # If using history, include previous messages
        if use_history and chat_history:
            context = "\n".join([
                f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}" 
                for i, msg in enumerate(chat_history[-6:])  # Last 3 exchanges
            ])
            full_prompt = f"{SYSTEM_PROMPT}\n\nConversation history:\n{context}\n\nUser: {prompt}\nAssistant:"
        
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            answer = response.text.strip()
            
            # Store in history
            chat_history.append(prompt)
            chat_history.append(answer)
            
            return answer
        
        return "I couldn't generate a response right now."
    
    except Exception as e:
        print(f"⚠ Gemini error: {e}")
        return "AI service is temporarily unavailable."

def clear_history():
    """Clear chat history to start fresh conversation"""
    chat_history.clear()
    print("✓ Chat history cleared")

def chat_mode():
    """Interactive chat mode"""
    print("=== Gemini Chat (type 'exit' to quit, 'clear' to reset) ===\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        if user_input.lower() == 'clear':
            clear_history()
            continue
        
        response = ask_gemini(user_input)
        print(f"AI: {response}\n")

# Test examples
if __name__ == "__main__":
    # Quick test
    print("=== Quick Test ===")
    print(ask_gemini("What is Python?"))
    print("\n" + "="*50 + "\n")
    
    # Follow-up question
    print(ask_gemini("Give me an example"))
    print("\n" + "="*50 + "\n")
    
    # Start interactive mode
    chat_mode()