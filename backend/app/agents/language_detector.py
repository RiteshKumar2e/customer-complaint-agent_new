"""
Language Detection Utility
Detects the language of user input and provides language-specific instructions for AI responses.
"""

def detect_language(text: str) -> str:
    """
    Detect the language of the input text.
    Returns: 'hinglish', 'hindi', 'english', or 'mixed'
    """
    if not text or not text.strip():
        return 'english'
    
    text = text.lower().strip()
    
    # Hindi/Devanagari character detection
    hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    
    # Common Hinglish patterns (Roman script Hindi words)
    hinglish_words = [
        'hai', 'nahi', 'kya', 'kaise', 'kab', 'kahan', 'kyun', 'kyu',
        'mera', 'meri', 'mere', 'tumhara', 'tumhari', 'tumhare',
        'aapka', 'aapki', 'aapke', 'hum', 'tum', 'aap',
        'kar', 'karo', 'karna', 'ho', 'hoga', 'hogi', 'hoge',
        'tha', 'thi', 'the', 'gaya', 'gayi', 'gaye',
        'chahiye', 'chahta', 'chahti', 'chahte',
        'problem', 'issue', 'help', 'please', 'kro', 'krna',
        'dikkat', 'pareshani', 'madad', 'zarurat', 'jarurat',
        'abhi', 'jaldi', 'turant', 'bahut', 'bohot', 'bht',
        'theek', 'thik', 'sahi', 'galat', 'accha', 'achha',
        'bhai', 'yaar', 'dost', 'sir', 'madam', 'ji',
        'paise', 'paisa', 'rupay', 'rupaye', 'payment',
        'order', 'delivery', 'product', 'service', 'account',
        'nhi', 'ni', 'na', 'haan', 'ha', 'haa', 'yes', 'no',
        'kuch', 'koi', 'sabhi', 'sab', 'sare', 'saare',
        'wala', 'wali', 'wale', 'waala', 'waali', 'waale',
        'se', 'ko', 'ka', 'ki', 'ke', 'me', 'mai', 'mein',
        'par', 'pe', 'tak', 'liye', 'liy', 'lye',
        'de', 'do', 'di', 'diya', 'diye', 'dena', 'deni',
        'le', 'lo', 'li', 'liya', 'liye', 'lena', 'leni',
        'raha', 'rahi', 'rahe', 'rhe', 'rhi', 'rha',
        'aaya', 'aayi', 'aaye', 'aya', 'ayi', 'aye',
        'chalu', 'chalao', 'chalta', 'chalti', 'chalte',
        'samajh', 'samjh', 'samjha', 'samjhi', 'samjhe',
        'dekh', 'dekho', 'dekha', 'dekhi', 'dekhe',
        'mil', 'mila', 'mili', 'mile', 'milta', 'milti', 'milte',
        'ban', 'bana', 'bani', 'bane', 'banta', 'banti', 'bante'
    ]
    
    # Count Hinglish words
    words = text.split()
    hinglish_count = sum(1 for word in words if word in hinglish_words)
    
    # Common English-only words (to distinguish from Hinglish)
    english_indicators = [
        'the', 'is', 'are', 'was', 'were', 'been', 'being',
        'have', 'has', 'had', 'will', 'would', 'should', 'could',
        'can', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'what', 'which', 'who',
        'when', 'where', 'why', 'how',
        'not', 'very', 'too', 'also', 'just', 'only',
        'about', 'after', 'before', 'during', 'while',
        'my', 'your', 'his', 'her', 'its', 'our', 'their'
    ]
    
    english_count = sum(1 for word in words if word in english_indicators)
    
    total_words = len(words)
    if total_words == 0:
        return 'english'
    
    # Calculate percentages
    hinglish_ratio = hinglish_count / total_words
    english_ratio = english_count / total_words
    hindi_char_ratio = hindi_chars / len(text)
    
    # Decision logic
    if hindi_char_ratio > 0.3:
        return 'hindi'
    elif hinglish_ratio > 0.15:
        return 'hinglish'
    elif hinglish_ratio > 0.05 and english_ratio > 0.1:
        return 'mixed'
    else:
        return 'english'


def get_language_instruction(language: str) -> str:
    """
    Get AI instruction based on detected language.
    """
    instructions = {
        'hinglish': """
CRITICAL LANGUAGE INSTRUCTION:
The user has written in HINGLISH (Hindi + English mix). You MUST respond in the SAME HINGLISH style.

RESPONSE RULES:
- Mix Hindi and English words naturally (e.g., "Aapki problem solve ho jayegi")
- Use Roman script (not Devanagari)
- Use common Hinglish words: hai, nahi, kya, kaise, aapka, mera, etc.
- Keep it conversational and friendly
- Use words like: problem, issue, help, solution, account, order, payment mixed with Hindi

EXAMPLES:
❌ WRONG: "Your issue will be resolved within 24 hours."
✅ CORRECT: "Aapki problem 24 hours mein solve ho jayegi."

❌ WRONG: "हम आपकी मदद करेंगे।"
✅ CORRECT: "Hum aapki help karenge."

❌ WRONG: "We apologize for the inconvenience."
✅ CORRECT: "Hume maafi hai is inconvenience ke liye."
""",
        'hindi': """
CRITICAL LANGUAGE INSTRUCTION:
The user has written in HINDI (Devanagari script). You MUST respond in HINDI using Devanagari script.

RESPONSE RULES:
- Use proper Hindi/Devanagari script (देवनागरी)
- Be formal and respectful
- Use शुद्ध हिंदी where possible
- Technical terms can be in English if needed

EXAMPLE:
❌ WRONG: "Your problem will be solved."
✅ CORRECT: "आपकी समस्या हल हो जाएगी।"
""",
        'mixed': """
CRITICAL LANGUAGE INSTRUCTION:
The user has written in a MIX of Hindi and English. You MUST respond in HINGLISH (Roman Hindi + English).

RESPONSE RULES:
- Use Hinglish (Roman script Hindi mixed with English)
- Match the user's casual, mixed style
- Use words like: aapka, problem, solve, help, hai, nahi, etc.

EXAMPLE:
✅ CORRECT: "Aapki complaint receive ho gayi hai. Hum jaldi se iska solution provide karenge."
""",
        'english': """
LANGUAGE INSTRUCTION:
The user has written in ENGLISH. Respond in clear, professional ENGLISH.
"""
    }
    
    return instructions.get(language, instructions['english'])


def get_language_example(language: str, context: str = "general") -> str:
    """
    Get example responses in the detected language.
    """
    examples = {
        'hinglish': {
            'complaint_received': "Dhanyavaad! Aapki complaint successfully receive ho gayi hai. Humari team jaldi se iska solution provide karegi.",
            'solution': "Aapki problem ko solve karne ke liye hum ye steps lenge: (1) Humari technical team 2 hours mein investigate karegi, (2) Aapko email se update milega, (3) 24 hours mein complete solution mil jayega.",
            'question': "Bilkul! Main aapki help karne ke liye yahan hoon. Aap apna question pooch sakte hain."
        },
        'hindi': {
            'complaint_received': "धन्यवाद! आपकी शिकायत सफलतापूर्वक प्राप्त हो गई है। हमारी टीम जल्द ही इसका समाधान प्रदान करेगी।",
            'solution': "आपकी समस्या को हल करने के लिए हम ये कदम उठाएंगे: (1) हमारी तकनीकी टीम 2 घंटे में जांच करेगी, (2) आपको ईमेल से अपडेट मिलेगा, (3) 24 घंटे में पूर्ण समाधान मिल जाएगा।",
            'question': "बिल्कुल! मैं आपकी मदद करने के लिए यहाँ हूँ। आप अपना प्रश्न पूछ सकते हैं।"
        },
        'mixed': {
            'complaint_received': "Thank you! Aapki complaint receive ho gayi hai. Hum jaldi response denge.",
            'solution': "Aapki issue solve karne ke liye: (1) Team investigate karegi, (2) Email update milega, (3) 24 hours mein solution milega.",
            'question': "Sure! Main help kar sakta hoon. Aap question puch sakte hain."
        },
        'english': {
            'complaint_received': "Thank you! Your complaint has been successfully received. Our team will provide a solution shortly.",
            'solution': "To solve your problem, we will: (1) Our technical team will investigate within 2 hours, (2) You'll receive email updates, (3) Complete solution within 24 hours.",
            'question': "Absolutely! I'm here to help you. Please feel free to ask your question."
        }
    }
    
    return examples.get(language, examples['english']).get(context, "")
