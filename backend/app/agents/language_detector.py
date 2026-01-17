import re
from typing import Literal

LanguageType = Literal['english', 'hindi', 'hinglish', 'mixed']

def detect_language(text: str) -> LanguageType:
    """
    Detects the language of the input text.
    Returns: 'hindi', 'english', 'hinglish', or 'mixed'
    
    Examples:
        >>> detect_language("My billing is wrong")
        'english'
        >>> detect_language("Mera bill galat hai")
        'hinglish'
        >>> detect_language("मेरा बिल गलत है")
        'hindi'
        >>> detect_language("My bill galat hai")
        'mixed'
    """
    if not text or not text.strip():
        return 'english'
    
    text_lower = text.lower()
    
    # Count Hindi/Devanagari characters
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    total_chars = len(re.sub(r'\s', '', text))
    
    if total_chars == 0:
        return 'english'
    
    hindi_ratio = hindi_chars / total_chars
    
    # Common Hinglish/Hindi words in Roman script
    hinglish_words = {
        # Verbs
        'hai', 'hain', 'tha', 'the', 'thi', 'hoga', 'hogi', 'hoge',
        'karna', 'karo', 'kare', 'karein', 'kiya', 'kiye', 'kar',
        'hona', 'ho', 'hua', 'hui', 'hue',
        'aana', 'aa', 'aaya', 'aayi', 'aayega', 'aayegi', 'aao',
        'jaana', 'ja', 'gaya', 'gayi', 'jayega', 'jayegi', 'jao',
        'lena', 'le', 'liya', 'liye', 'lega', 'legi', 'lo',
        'dena', 'de', 'diya', 'diye', 'dega', 'degi', 'do',
        'milna', 'mile', 'mila', 'mili', 'milega', 'milegi',
        'chahiye', 'chahte', 'chahta', 'chahti', 'chahiye',
        'samajh', 'samjha', 'samjhi', 'samjho', 'samajhna',
        'dekh', 'dekha', 'dekhi', 'dekho', 'dekhna',
        'sun', 'suna', 'suni', 'suno', 'sunna',
        'bol', 'bola', 'boli', 'bolo', 'bolna',
        'kar', 'kara', 'kari', 'karo', 'karna',
        
        # Pronouns & Possessives
        'mera', 'meri', 'mere', 'mujhe', 'main', 'mai',
        'tera', 'teri', 'tere', 'tujhe', 'tu', 'tum',
        'aapka', 'aapki', 'aapke', 'aap', 'aapko',
        'humara', 'humari', 'humare', 'hum', 'humko',
        'tumhara', 'tumhari', 'tumhare', 'tumko',
        'uska', 'uski', 'uske', 'usne', 'usको',
        
        # Postpositions
        'ka', 'ki', 'ke', 'ko', 'se', 'mein', 'par', 'pe',
        'tak', 'liye', 'saath', 'bina', 'baad', 'pehle',
        
        # Conjunctions
        'aur', 'ya', 'lekin', 'par', 'kyunki', 'isliye',
        'agar', 'to', 'toh', 'tab', 'jab',
        
        # Question words
        'kya', 'kaise', 'kab', 'kahan', 'kyun', 'kyu', 'kaun',
        'kitna', 'kitni', 'kitne', 'kaunsa', 'kaunsi',
        
        # Negation
        'nahi', 'nahin', 'na', 'mat', 'naa',
        
        # Affirmation
        'haan', 'han', 'ha', 'ji', 'theek', 'sahi', 'achha', 'accha',
        
        # Adjectives/Adverbs
        'bahut', 'bohot', 'thoda', 'jyada', 'zyada', 'kam',
        'bada', 'badi', 'bade', 'chota', 'choti', 'chote',
        'achha', 'accha', 'achhi', 'achhe', 'bura', 'buri', 'bure',
        'galat', 'sahi', 'theek', 'thik',
        
        # Common nouns (These are often used in Hinglish but are primarily English)
        'account', 'delivery', 'payment', 'support',
        
        # Others
        'shukriya', 'shukriyaa', 'dhanyavaad', 'maaf', 'maafi',
    }
    
    # Very specific Hinglish markers (Verbs/Pronouns that almost never appear in pure English)
    specific_hinglish = {
        'hai', 'hain', 'tha', 'thi', 'the', 'hoga', 'hogi', 'karna', 'karo', 'karein', 
        'mera', 'meri', 'mere', 'mujhe', 'humara', 'aapka', 'uska', 'iska',
        'kya', 'kaise', 'kab', 'kahan', 'kyun', 'kyu', 'toh', 'aur', 'nahi', 'nahin'
    }
    
    # Count Hinglish words
    words = text_lower.split()
    total_words = len(words)
    if total_words == 0: return 'english'
    
    hinglish_count = sum(1 for word in words if word in hinglish_words)
    specific_count = sum(1 for word in words if word in specific_hinglish)
    
    hinglish_ratio = hinglish_count / total_words
    
    # Decision logic
    if hindi_ratio > 0.4:
        # High Devanagari ratio
        return 'hindi'
    elif specific_count >= 1 or (hinglish_ratio > 0.4 and total_words > 2):
        # Has specific Hindi markers OR high general Hinglish word ratio in longer text
        return 'hinglish'
    elif hindi_ratio > 0.1 or hinglish_ratio > 0.2:
        return 'mixed'
    else:
        return 'english'


def get_language_instruction(language: LanguageType) -> str:
    """Returns instruction for AI to respond in specific language"""
    instructions = {
        'english': "Respond in professional English only.",
        'hindi': "पूरी तरह से हिंदी (देवनागरी लिपि) में जवाब दें। कोई अंग्रेजी शब्द न use करें।",
        'hinglish': "Respond in Hinglish (Hindi words written in Roman/English script). Example: 'Aapki complaint receive ho gayi hai. Hum jaldi resolve karenge.' Use natural Hinglish mixing.",
        'mixed': "Respond in mixed English-Hindi style, matching the user's writing pattern. Use both English and Hinglish words naturally, just like the user did."
    }
    return instructions.get(language, instructions['english'])


def get_language_example(language: LanguageType, context: str = 'complaint_received') -> str:
    """Returns example response in specific language for given context"""
    examples = {
        'complaint_received': {
            'english': "Thank you for contacting us. We've received your complaint and our team is reviewing it carefully.",
            'hindi': "हमसे संपर्क करने के लिए धन्यवाद। हमने आपकी शिकायत प्राप्त कर ली है और हमारी टीम इसकी समीक्षा कर रही है।",
            'hinglish': "Humse contact karne ke liye dhanyavaad. Humne aapki complaint receive kar li hai aur humari team carefully review kar rahi hai.",
            'mixed': "Thank you for contacting us. Humne aapki complaint receive kar li hai aur team review kar rahi hai."
        },
        'billing_issue': {
            'english': "I sincerely apologize for the billing error. Our billing team will review your account within 4 hours.",
            'hindi': "बिलिंग त्रुटि के लिए मुझे सचमुच खेद है। हमारी बिलिंग टीम 4 घंटों में आपके खाते की समीक्षा करेगी।",
            'hinglish': "Billing error ke liye mujhe sachme maafi hai. Humari billing team 4 hours mein aapke account ko review karegi.",
            'mixed': "Billing error ke liye I sincerely apologize. Humari team 4 hours mein review karegi."
        },
        'delivery_delay': {
            'english': "We apologize for the delivery delay. Your order has been marked for priority delivery.",
            'hindi': "डिलीवरी में देरी के लिए हमें खेद है। आपके ऑर्डर को प्राथमिकता डिलीवरी के लिए चिह्नित किया गया है।",
            'hinglish': "Delivery delay ke liye hume maafi hai. Aapka order priority delivery ke liye mark ho gaya hai.",
            'mixed': "Delivery delay ke lिए we apologize. Aapka order priority delivery ke liye mark ho gaya hai."
        }
    }
    
    context_examples = examples.get(context, examples['complaint_received'])
    return context_examples.get(language, context_examples['english'])



# Test function
if __name__ == "__main__":
    test_cases = [
        ("My billing is wrong", "english"),
        ("Mera bill galat hai", "hinglish"),
        ("मेरा बिल गलत है", "hindi"),
        ("My bill galat hai kya", "mixed"),
        ("Delivery nahi aayi hai", "hinglish"),
        ("Order kab milega?", "hinglish"),
        ("I need help with my order", "english"),
        ("Help chahiye order ke saath", "mixed"),
        ("Aapka support bahut achha hai", "hinglish"),
        ("यह सेवा बहुत अच्छी है", "hindi"),
        ("This service bahut achhi hai", "mixed"),
        ("Kya aap meri help kar sakte hain?", "hinglish"),
        ("Can you help me please?", "english"),
        ("Mujhe complaint karna hai", "hinglish"),
        ("I want to complain about delivery", "english"),
    ]
    
    print("🌐 Language Detection Tests:\n")
    print(f"{'Input':<45} {'Detected':<12} {'Expected':<12} {'Match'}")
    print("-" * 80)
    
    correct = 0
    for text, expected in test_cases:
        detected = detect_language(text)
        match = "✅" if detected == expected else "❌"
        if detected == expected:
            correct += 1
        print(f"{text:<45} {detected:<12} {expected:<12} {match}")
    
    print("-" * 80)
    print(f"\nAccuracy: {correct}/{len(test_cases)} ({100*correct//len(test_cases)}%)")
