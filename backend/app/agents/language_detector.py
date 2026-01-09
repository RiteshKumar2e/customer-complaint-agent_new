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
        
        # Common nouns
        'problem', 'issue', 'complaint', 'help', 'support',
        'order', 'delivery', 'payment', 'bill', 'account',
        'time', 'din', 'baar', 'cheez', 'baat',
        
        # Others
        'please', 'plz', 'pls', 'thanks', 'thank', 'sorry',
        'dhanyavaad', 'shukriya', 'maaf', 'maafi',
    }
    
    # Count Hinglish words
    words = text_lower.split()
    hinglish_count = sum(1 for word in words if word in hinglish_words)
    hinglish_ratio = hinglish_count / len(words) if words else 0
    
    # Decision logic
    if hindi_ratio > 0.5:
        # More than 50% Devanagari characters
        return 'hindi'
    elif hinglish_ratio > 0.25:
        # Significant Hinglish words (>25%)
        return 'hinglish'
    elif hindi_ratio > 0.1 or hinglish_ratio > 0.1:
        # Some Hindi/Hinglish mixed with English
        return 'mixed'
    else:
        # Mostly English
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
