"""
Test script to verify language matching in chatbot responses
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.agents.chat_agent import handle_chat_message
from app.agents.language_detector import detect_language

async def test_language_matching():
    """Test chatbot responses in different languages"""
    
    test_cases = [
        # English tests
        ("How does Quickfix work?", "english"),
        ("What are the features?", "english"),
        ("Can you help me?", "english"),
        
        # Hinglish tests
        ("Quickfix kaise kaam karta hai?", "hinglish"),
        ("Kya features hain?", "hinglish"),
        ("Mujhe help chahiye", "hinglish"),
        
        # Hindi tests
        ("क्विकफिक्स कैसे काम करता है?", "hindi"),
        ("क्या विशेषताएं हैं?", "hindi"),
        ("मुझे मदद चाहिए", "hindi"),
        
        # Mixed tests
        ("How does ye system kaam karta hai?", "mixed"),
    ]
    
    print("=" * 80)
    print("🧪 LANGUAGE MATCHING TEST")
    print("=" * 80)
    print()
    
    for message, expected_lang in test_cases:
        print(f"📝 USER INPUT: {message}")
        
        # Detect language
        detected = detect_language(message)
        print(f"🌐 DETECTED LANGUAGE: {detected} (Expected: {expected_lang})")
        
        # Get chatbot response
        try:
            response = await handle_chat_message(message)
            print(f"🤖 BOT RESPONSE: {response.get('response', 'No response')}")
            print(f"📊 RESPONSE LANGUAGE: {response.get('language', 'Not specified')}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 80)
        print()

if __name__ == "__main__":
    asyncio.run(test_language_matching())
