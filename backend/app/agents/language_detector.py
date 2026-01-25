import re
from typing import Literal

# Expanded to 20 languages for comprehensive multilingual support
LanguageType = Literal[
    'english', 'hindi', 'hinglish', 'mixed',
    'kannada', 'tamil', 'bengali', 'telugu', 'marathi', 
    'gujarati', 'punjabi', 'malayalam', 'odia', 'assamese',
    'urdu', 'sanskrit', 'spanish', 'french', 'german', 
    'arabic', 'chinese'
]

def detect_language(text: str) -> LanguageType:
    """
    Detects the language of the input text from 20 supported languages.
    Returns: Language code as LanguageType
    
    Supported Languages:
    - Indian: english, hindi, hinglish, kannada, tamil, bengali, telugu, marathi, 
              gujarati, punjabi, malayalam, odia, assamese, urdu, sanskrit
    - International: spanish, french, german, arabic, chinese
    
    Examples:
        >>> detect_language("My billing is wrong")
        'english'
        >>> detect_language("Mera bill galat hai")
        'hinglish'
        >>> detect_language("मेरा बिल गलत है")
        'hindi'
        >>> detect_language("ನನ್ನ ಬಿಲ್ ತಪ್ಪಾಗಿದೆ")
        'kannada'
        >>> detect_language("என் பில் தவறானது")
        'tamil'
    """
    if not text or not text.strip():
        return 'english'
    
    text_lower = text.lower()
    
    # Unicode ranges for different scripts
    script_ranges = {
        'devanagari': r'[\u0900-\u097F]',  # Hindi, Sanskrit, Marathi
        'bengali': r'[\u0980-\u09FF]',      # Bengali, Assamese
        'tamil': r'[\u0B80-\u0BFF]',        # Tamil
        'telugu': r'[\u0C00-\u0C7F]',       # Telugu
        'kannada': r'[\u0C80-\u0CFF]',      # Kannada
        'malayalam': r'[\u0D00-\u0D7F]',    # Malayalam
        'gujarati': r'[\u0A80-\u0AFF]',     # Gujarati
        'gurmukhi': r'[\u0A00-\u0A7F]',     # Punjabi
        'odia': r'[\u0B00-\u0B7F]',         # Odia
        'arabic': r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]',  # Arabic, Urdu
        'chinese': r'[\u4E00-\u9FFF\u3400-\u4DBF]',  # Chinese
    }
    
    # Count characters for each script
    total_chars = len(re.sub(r'\s', '', text))
    if total_chars == 0:
        return 'english'
    
    script_counts = {}
    for script_name, pattern in script_ranges.items():
        count = len(re.findall(pattern, text))
        if count > 0:
            script_counts[script_name] = count / total_chars
    
    # Check for specific scripts first
    if 'tamil' in script_counts and script_counts['tamil'] > 0.3:
        return 'tamil'
    if 'kannada' in script_counts and script_counts['kannada'] > 0.3:
        return 'kannada'
    if 'telugu' in script_counts and script_counts['telugu'] > 0.3:
        return 'telugu'
    if 'malayalam' in script_counts and script_counts['malayalam'] > 0.3:
        return 'malayalam'
    if 'bengali' in script_counts and script_counts['bengali'] > 0.3:
        # Distinguish between Bengali and Assamese (both use same script)
        assamese_words = {'অসমীয়া', 'অসম', 'মই', 'আপুনি'}
        if any(word in text for word in assamese_words):
            return 'assamese'
        return 'bengali'
    if 'gujarati' in script_counts and script_counts['gujarati'] > 0.3:
        return 'gujarati'
    if 'gurmukhi' in script_counts and script_counts['gurmukhi'] > 0.3:
        return 'punjabi'
    if 'odia' in script_counts and script_counts['odia'] > 0.3:
        return 'odia'
    if 'chinese' in script_counts and script_counts['chinese'] > 0.3:
        return 'chinese'
    
    # Check for Arabic script (Urdu and Arabic)
    if 'arabic' in script_counts and script_counts['arabic'] > 0.3:
        # Distinguish between Urdu and Arabic
        urdu_words = {'ہے', 'ہیں', 'کا', 'کی', 'کے', 'میں', 'سے', 'نے', 'کو', 'ہوں'}
        if any(word in text for word in urdu_words):
            return 'urdu'
        return 'arabic'
    
    # Check for Devanagari script (Hindi, Sanskrit, Marathi)
    if 'devanagari' in script_counts and script_counts['devanagari'] > 0.4:
        # Distinguish between Hindi, Sanskrit, and Marathi
        sanskrit_words = {'संस्कृतम्', 'भवति', 'अस्ति', 'किम्', 'कथम्', 'यत्', 'तत्'}
        marathi_words = {'आहे', 'आहेत', 'होते', 'होता', 'मी', 'तू', 'तुम्ही', 'माझा', 'माझी'}
        
        if any(word in text for word in sanskrit_words):
            return 'sanskrit'
        elif any(word in text for word in marathi_words):
            return 'marathi'
        return 'hindi'
    
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
        'chahiye', 'chahte', 'chahta', 'chahti',
        'samajh', 'samjha', 'samjhi', 'samjho', 'samajhna',
        'dekh', 'dekha', 'dekhi', 'dekho', 'dekhna',
        'sun', 'suna', 'suni', 'suno', 'sunna',
        'bol', 'bola', 'boli', 'bolo', 'bolna',
        
        # Pronouns & Possessives
        'mera', 'meri', 'mere', 'mujhe', 'main', 'mai',
        'tera', 'teri', 'tere', 'tujhe', 'tu', 'tum',
        'aapka', 'aapki', 'aapke', 'aap', 'aapko',
        'humara', 'humari', 'humare', 'hum', 'humko',
        'tumhara', 'tumhari', 'tumhare', 'tumko',
        'uska', 'uski', 'uske', 'usne',
        
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
        
        # Others
        'shukriya', 'shukriyaa', 'dhanyavaad', 'maaf', 'maafi',
    }
    
    # Spanish common words
    spanish_words = {
        'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'al',
        'es', 'está', 'son', 'están', 'ser', 'estar', 'hay',
        'mi', 'tu', 'su', 'nuestro', 'vuestro',
        'qué', 'cómo', 'cuándo', 'dónde', 'por', 'para',
        'sí', 'no', 'gracias', 'por favor', 'hola', 'adiós',
        'muy', 'más', 'menos', 'también', 'pero', 'porque'
    }
    
    # French common words
    french_words = {
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de',
        'est', 'sont', 'être', 'avoir', 'il', 'elle', 'nous', 'vous',
        'je', 'tu', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
        'qui', 'que', 'quoi', 'où', 'quand', 'comment', 'pourquoi',
        'oui', 'non', 'merci', 'bonjour', 'au revoir',
        'très', 'plus', 'moins', 'aussi', 'mais', 'parce que'
    }
    
    # German common words
    german_words = {
        'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einen',
        'ist', 'sind', 'sein', 'haben', 'hat', 'wird', 'werden',
        'ich', 'du', 'er', 'sie', 'wir', 'ihr', 'mein', 'dein', 'sein',
        'was', 'wie', 'wann', 'wo', 'warum', 'wer',
        'ja', 'nein', 'danke', 'bitte', 'hallo', 'auf wiedersehen',
        'sehr', 'mehr', 'weniger', 'auch', 'aber', 'weil', 'und', 'oder'
    }
    
    # Very specific Hinglish markers
    specific_hinglish = {
        'hai', 'hain', 'tha', 'thi', 'the', 'hoga', 'hogi', 'karna', 'karo', 'karein', 
        'mera', 'meri', 'mere', 'mujhe', 'humara', 'aapka', 'uska', 'iska',
        'kya', 'kaise', 'kab', 'kahan', 'kyun', 'kyu', 'toh', 'aur', 'nahi', 'nahin'
    }
    
    # Count words for each language
    words = text_lower.split()
    total_words = len(words)
    if total_words == 0:
        return 'english'
    
    hinglish_count = sum(1 for word in words if word in hinglish_words)
    specific_count = sum(1 for word in words if word in specific_hinglish)
    spanish_count = sum(1 for word in words if word in spanish_words)
    french_count = sum(1 for word in words if word in french_words)
    german_count = sum(1 for word in words if word in german_words)
    
    hinglish_ratio = hinglish_count / total_words
    spanish_ratio = spanish_count / total_words
    french_ratio = french_count / total_words
    german_ratio = german_count / total_words
    
    # Check for European languages
    if spanish_ratio > 0.3:
        return 'spanish'
    if french_ratio > 0.3:
        return 'french'
    if german_ratio > 0.3:
        return 'german'
    
    # Check for Hinglish/Mixed
    if specific_count >= 1 or (hinglish_ratio > 0.4 and total_words > 2):
        return 'hinglish'
    elif hinglish_ratio > 0.2:
        return 'mixed'
    else:
        return 'english'


def get_language_instruction(language: LanguageType) -> str:
    """Returns instruction for AI to respond in specific language"""
    instructions = {
        'english': "Respond in professional English only.",
        'hindi': "पूरी तरह से हिंदी (देवनागरी लिपि) में जवाब दें। कोई अंग्रेजी शब्द न use करें।",
        'hinglish': "Respond in Hinglish (Hindi words written in Roman/English script). Example: 'Aapki complaint receive ho gayi hai. Hum jaldi resolve karenge.' Use natural Hinglish mixing.",
        'mixed': "Respond in mixed English-Hindi style, matching the user's writing pattern. Use both English and Hinglish words naturally, just like the user did.",
        
        # Indian Languages
        'kannada': "ಕನ್ನಡದಲ್ಲಿ ಮಾತ್ರ ಉತ್ತರಿಸಿ। Respond completely in Kannada script.",
        'tamil': "தமிழில் மட்டும் பதிலளிக்கவும். Respond completely in Tamil script.",
        'bengali': "শুধুমাত্র বাংলায় উত্তর দিন। Respond completely in Bengali script.",
        'telugu': "తెలుగులో మాత్రమే సమాధానం ఇవ్వండి। Respond completely in Telugu script.",
        'marathi': "फक्त मराठीत उत्तर द्या। Respond completely in Marathi (Devanagari) script.",
        'gujarati': "ફક્ત ગુજરાતીમાં જવાબ આપો। Respond completely in Gujarati script.",
        'punjabi': "ਕੇਵਲ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ। Respond completely in Punjabi (Gurmukhi) script.",
        'malayalam': "മലയാളത്തിൽ മാത്രം മറുപടി നൽകുക। Respond completely in Malayalam script.",
        'odia': "କେବଳ ଓଡ଼ିଆରେ ଉତ୍ତର ଦିଅନ୍ତୁ। Respond completely in Odia script.",
        'assamese': "কেৱল অসমীয়াত উত্তৰ দিয়ক। Respond completely in Assamese script.",
        'urdu': "صرف اردو میں جواب دیں۔ Respond completely in Urdu (Arabic) script, right-to-left.",
        'sanskrit': "केवलं संस्कृतेन उत्तरं ददातु। Respond completely in Sanskrit (Devanagari) script.",
        
        # International Languages
        'spanish': "Responda solo en español profesional. Use formal language appropriate for customer service.",
        'french': "Répondez uniquement en français professionnel. Utilisez un langage formel approprié pour le service client.",
        'german': "Antworten Sie nur auf professionellem Deutsch. Verwenden Sie eine formelle Sprache, die für den Kundenservice geeignet ist.",
        'arabic': "الرد باللغة العربية الفصحى فقط. استخدم لغة رسمية مناسبة لخدمة العملاء. Write right-to-left.",
        'chinese': "仅用专业中文回复。使用适合客户服务的正式语言。Respond in Simplified Chinese.",
    }
    return instructions.get(language, instructions['english'])


def get_language_example(language: LanguageType, context: str = 'complaint_received') -> str:
    """Returns example response in specific language for given context"""
    examples = {
        'complaint_received': {
            'english': "Thank you for contacting us. We've received your complaint and our team is reviewing it carefully.",
            'hindi': "हमसे संपर्क करने के लिए धन्यवाद। हमने आपकी शिकायत प्राप्त कर ली है और हमारी टीम इसकी समीक्षा कर रही है।",
            'hinglish': "Humse contact karne ke liye dhanyavaad. Humne aapki complaint receive kar li hai aur humari team carefully review kar rahi hai.",
            'mixed': "Thank you for contacting us. Humne aapki complaint receive kar li hai aur team review kar rahi hai.",
            'kannada': "ನಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ದೂರನ್ನು ನಾವು ಸ್ವೀಕರಿಸಿದ್ದೇವೆ ಮತ್ತು ನಮ್ಮ ತಂಡವು ಅದನ್ನು ಎಚ್ಚರಿಕೆಯಿಂದ ಪರಿಶೀಲಿಸುತ್ತಿದೆ.",
            'tamil': "எங்களை தொடர்பு கொண்டதற்கு நன்றி. உங்கள் புகாரை நாங்கள் பெற்றுள்ளோம் மற்றும் எங்கள் குழு அதை கவனமாக மதிப்பாய்வு செய்து வருகிறது.",
            'bengali': "আমাদের সাথে যোগাযোগ করার জন্য ধন্যবাদ। আমরা আপনার অভিযোগ পেয়েছি এবং আমাদের দল সাবধানে এটি পর্যালোচনা করছে।",
            'telugu': "మమ్మల్ని సంప్రదించినందుకు ధన్యవాదాలు. మేము మీ ఫిర్యాదును స్వీకరించాము మరియు మా బృందం దానిని జాగ్రత్తగా సమీక్షిస్తోంది.",
            'marathi': "आमच्याशी संपर्क साधल्याबद्दल धन्यवाद. आम्हाला तुमची तक्रार मिळाली आहे आणि आमची टीम काळजीपूर्वक त्याचे पुनरावलोकन करत आहे.",
            'gujarati': "અમારો સંપર્ક કરવા બદલ આભાર. અમે તમારી ફરિયાદ પ્રાપ્ત કરી છે અને અમારી ટીમ તેની કાળજીપૂર્વક સમીક્ષા કરી રહી છે.",
            'punjabi': "ਸਾਡੇ ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ ਧੰਨਵਾਦ। ਅਸੀਂ ਤੁਹਾਡੀ ਸ਼ਿਕਾਇਤ ਪ੍ਰਾਪਤ ਕਰ ਲਈ ਹੈ ਅਤੇ ਸਾਡੀ ਟੀਮ ਧਿਆਨ ਨਾਲ ਇਸਦੀ ਸਮੀਖਿਆ ਕਰ ਰਹੀ ਹੈ।",
            'malayalam': "ഞങ്ങളെ ബന്ധപ്പെട്ടതിന് നന്ദി. ഞങ്ങൾ നിങ്ങളുടെ പരാതി സ്വീകരിച്ചു, ഞങ്ങളുടെ ടീം അത് ശ്രദ്ധാപൂർവ്വം അവലോകനം ചെയ്യുന്നു.",
            'odia': "ଆମକୁ ଯୋଗାଯୋଗ କରିଥିବାରୁ ଧନ୍ୟବାଦ। ଆମେ ଆପଣଙ୍କର ଅଭିଯୋଗ ଗ୍ରହଣ କରିଛୁ ଏବଂ ଆମର ଦଳ ଏହାକୁ ଯତ୍ନର ସହିତ ସମୀକ୍ଷା କରୁଛି।",
            'assamese': "আমাৰ সৈতে যোগাযোগ কৰাৰ বাবে ধন্যবাদ। আমি আপোনাৰ অভিযোগ লাভ কৰিছো আৰু আমাৰ দলে সাৱধানে ইয়াক পৰ্যালোচনা কৰি আছে।",
            'urdu': "ہم سے رابطہ کرنے کا شکریہ۔ ہمیں آپ کی شکایت موصول ہو گئی ہے اور ہماری ٹیم اس کا بغور جائزہ لے رہی ہے۔",
            'sanskrit': "अस्माभिः सह सम्पर्कं कृतवन्तः इति धन्यवादः। वयं भवतः परिवादं प्राप्तवन्तः अस्माकं दलं च सावधानतया तस्य समीक्षां करोति।",
            'spanish': "Gracias por contactarnos. Hemos recibido su queja y nuestro equipo la está revisando cuidadosamente.",
            'french': "Merci de nous avoir contactés. Nous avons reçu votre plainte et notre équipe l'examine attentivement.",
            'german': "Vielen Dank für Ihre Kontaktaufnahme. Wir haben Ihre Beschwerde erhalten und unser Team prüft sie sorgfältig.",
            'arabic': "شكراً لتواصلك معنا. لقد تلقينا شكواك ويقوم فريقنا بمراجعتها بعناية.",
            'chinese': "感谢您联系我们。我们已收到您的投诉，我们的团队正在仔细审查。",
        },
        'billing_issue': {
            'english': "I sincerely apologize for the billing error. Our billing team will review your account within 4 hours.",
            'hindi': "बिलिंग त्रुटि के लिए मुझे सचमुच खेद है। हमारी बिलिंग टीम 4 घंटों में आपके खाते की समीक्षा करेगी।",
            'hinglish': "Billing error ke liye mujhe sachme maafi hai. Humari billing team 4 hours mein aapke account ko review karegi.",
            'mixed': "Billing error ke liye I sincerely apologize. Humari team 4 hours mein review karegi.",
            'kannada': "ಬಿಲ್ಲಿಂಗ್ ದೋಷಕ್ಕಾಗಿ ನಾನು ಪ್ರಾಮಾಣಿಕವಾಗಿ ಕ್ಷಮೆ ಕೇಳುತ್ತೇನೆ. ನಮ್ಮ ಬಿಲ್ಲಿಂಗ್ ತಂಡವು 4 ಗಂಟೆಗಳಲ್ಲಿ ನಿಮ್ಮ ಖಾತೆಯನ್ನು ಪರಿಶೀಲಿಸುತ್ತದೆ.",
            'tamil': "பில்லிங் பிழைக்கு நான் மனதார மன்னிப்பு கேட்கிறேன். எங்கள் பில்லிங் குழு 4 மணி நேரத்தில் உங்கள் கணக்கை மதிப்பாய்வு செய்யும்.",
            'bengali': "বিলিং ত্রুটির জন্য আমি আন্তরিকভাবে ক্ষমাপ্রার্থী। আমাদের বিলিং দল 4 ঘন্টার মধ্যে আপনার অ্যাকাউন্ট পর্যালোচনা করবে।",
            'telugu': "బిల్లింగ్ లోపం కోసం నేను హృదయపూర్వకంగా క్షమాపణలు కోరుతున్నాను. మా బిల్లింగ్ బృందం 4 గంటల్లో మీ ఖాతాను సమీక్షిస్తుంది.",
            'marathi': "बिलिंग त्रुटीबद्दल मी मनापासून माफी मागतो. आमची बिलिंग टीम 4 तासांत तुमच्या खात्याचे पुनरावलोकन करेल.",
            'gujarati': "બિલિંગ ભૂલ માટે હું નિષ્ઠાપૂર્વક માફી માંગુ છું. અમારી બિલિંગ ટીમ 4 કલાકમાં તમારા એકાઉન્ટની સમીક્ષા કરશે.",
            'punjabi': "ਬਿਲਿੰਗ ਗਲਤੀ ਲਈ ਮੈਂ ਦਿਲੋਂ ਮੁਆਫੀ ਮੰਗਦਾ ਹਾਂ। ਸਾਡੀ ਬਿਲਿੰਗ ਟੀਮ 4 ਘੰਟਿਆਂ ਵਿੱਚ ਤੁਹਾਡੇ ਖਾਤੇ ਦੀ ਸਮੀਖਿਆ ਕਰੇਗੀ।",
            'malayalam': "ബില്ലിംഗ് പിശകിന് ഞാൻ ആത്മാർത്ഥമായി ക്ഷമ ചോദിക്കുന്നു. ഞങ്ങളുടെ ബില്ലിംഗ് ടീം 4 മണിക്കൂറിനുള്ളിൽ നിങ്ങളുടെ അക്കൗണ്ട് അവലോകനം ചെയ്യും.",
            'odia': "ବିଲିଂ ତ୍ରୁଟି ପାଇଁ ମୁଁ ଆନ୍ତରିକତାର ସହିତ କ୍ଷମା ମାଗୁଛି। ଆମର ବିଲିଂ ଦଳ 4 ଘଣ୍ଟା ମଧ୍ୟରେ ଆପଣଙ୍କର ଖାତା ସମୀକ୍ଷା କରିବ।",
            'assamese': "বিলিং ত্ৰুটিৰ বাবে মই আন্তৰিকভাৱে ক্ষমা বিচাৰিছো। আমাৰ বিলিং দলে 4 ঘণ্টাৰ ভিতৰত আপোনাৰ একাউণ্ট পৰ্যালোচনা কৰিব।",
            'urdu': "بلنگ کی غلطی کے لیے میں مخلصانہ معذرت خواہ ہوں۔ ہماری بلنگ ٹیم 4 گھنٹوں میں آپ کے اکاؤنٹ کا جائزہ لے گی۔",
            'sanskrit': "गणना दोषस्य कृते अहं हार्दिकतया क्षमां याचे। अस्माकं गणना दलं चतुर्षु घण्टेषु भवतः लेखायाः समीक्षां करिष्यति।",
            'spanish': "Me disculpo sinceramente por el error de facturación. Nuestro equipo de facturación revisará su cuenta en 4 horas.",
            'french': "Je m'excuse sincèrement pour l'erreur de facturation. Notre équipe de facturation examinera votre compte dans 4 heures.",
            'german': "Ich entschuldige mich aufrichtig für den Abrechnungsfehler. Unser Abrechnungsteam wird Ihr Konto innerhalb von 4 Stunden überprüfen.",
            'arabic': "أعتذر بصدق عن خطأ الفواتير. سيقوم فريق الفواتير لدينا بمراجعة حسابك خلال 4 ساعات.",
            'chinese': "我对账单错误深表歉意。我们的账单团队将在4小时内审查您的账户。",
        },
        'delivery_delay': {
            'english': "We apologize for the delivery delay. Your order has been marked for priority delivery.",
            'hindi': "डिलीवरी में देरी के लिए हमें खेद है। आपके ऑर्डर को प्राथमिकता डिलीवरी के लिए चिह्नित किया गया है।",
            'hinglish': "Delivery delay ke liye hume maafi hai. Aapka order priority delivery ke liye mark ho gaya hai.",
            'mixed': "Delivery delay ke लिए we apologize. Aapka order priority delivery ke liye mark ho gaya hai.",
            'kannada': "ವಿತರಣೆ ವಿಳಂಬಕ್ಕಾಗಿ ನಾವು ಕ್ಷಮೆ ಕೇಳುತ್ತೇವೆ. ನಿಮ್ಮ ಆರ್ಡರ್ ಅನ್ನು ಆದ್ಯತೆಯ ವಿತರಣೆಗಾಗಿ ಗುರುತಿಸಲಾಗಿದೆ.",
            'tamil': "டெலிவரி தாமதத்திற்கு நாங்கள் மன்னிப்பு கேட்கிறோம். உங்கள் ஆர்டர் முன்னுரிமை டெலிவரிக்காக குறிக்கப்பட்டுள்ளது.",
            'bengali': "ডেলিভারি বিলম্বের জন্য আমরা ক্ষমাপ্রার্থী। আপনার অর্ডার অগ্রাধিকার ডেলিভারির জন্য চিহ্নিত করা হয়েছে।",
            'telugu': "డెలివరీ ఆలస్యానికి మేము క్షమాపణలు కోరుతున్నాము. మీ ఆర్డర్ ప్రాధాన్యత డెలివరీ కోసం గుర్తించబడింది.",
            'marathi': "वितरणात विलंब झाल्याबद्दल आम्ही दिलगीर आहोत. तुमची ऑर्डर प्राधान्य वितरणासाठी चिन्हांकित केली गेली आहे.",
            'gujarati': "ડિલિવરીમાં વિલંબ બદલ અમે માફી માંગીએ છીએ. તમારો ઓર્ડર પ્રાથમિકતા ડિલિવરી માટે ચિહ્નિત કરવામાં આવ્યો છે.",
            'punjabi': "ਡਿਲੀਵਰੀ ਵਿੱਚ ਦੇਰੀ ਲਈ ਅਸੀਂ ਮੁਆਫੀ ਮੰਗਦੇ ਹਾਂ। ਤੁਹਾਡੇ ਆਰਡਰ ਨੂੰ ਤਰਜੀਹੀ ਡਿਲੀਵਰੀ ਲਈ ਚਿੰਨ੍ਹਿਤ ਕੀਤਾ ਗਿਆ ਹੈ।",
            'malayalam': "ഡെലിവറി കാലതാമസത്തിന് ഞങ്ങൾ ക്ഷമ ചോദിക്കുന്നു. നിങ്ങളുടെ ഓർഡർ മുൻഗണന ഡെലിവറിക്കായി അടയാളപ്പെടുത്തിയിരിക്കുന്നു.",
            'odia': "ବିତରଣ ବିଳମ୍ବ ପାଇଁ ଆମେ କ୍ଷମା ମାଗୁଛୁ। ଆପଣଙ୍କର ଅର୍ଡର ପ୍ରାଥମିକତା ବିତରଣ ପାଇଁ ଚିହ୍ନିତ ହୋଇଛି।",
            'assamese': "ডেলিভাৰী পলম হোৱাৰ বাবে আমি ক্ষমা বিচাৰিছো। আপোনাৰ অৰ্ডাৰ অগ্ৰাধিকাৰ ডেলিভাৰীৰ বাবে চিহ্নিত কৰা হৈছে।",
            'urdu': "ڈیلیوری میں تاخیر کے لیے ہم معذرت خواہ ہیں۔ آپ کے آرڈر کو ترجیحی ڈیلیوری کے لیے نشان زد کر دیا گیا ہے۔",
            'sanskrit': "वितरणे विलम्बस्य कृते वयं क्षमां याचामहे। भवतः आदेशः प्राथमिकता वितरणाय चिह्नितः अस्ति।",
            'spanish': "Nos disculpamos por el retraso en la entrega. Su pedido ha sido marcado para entrega prioritaria.",
            'french': "Nous nous excusons pour le retard de livraison. Votre commande a été marquée pour une livraison prioritaire.",
            'german': "Wir entschuldigen uns für die Lieferverzögerung. Ihre Bestellung wurde für vorrangige Lieferung markiert.",
            'arabic': "نعتذر عن تأخير التسليم. تم وضع علامة على طلبك للتسليم ذي الأولوية.",
            'chinese': "我们对交付延迟表示歉意。您的订单已被标记为优先交付。",
        }
    }
    
    context_examples = examples.get(context, examples['complaint_received'])
    return context_examples.get(language, context_examples['english'])



# Test function
if __name__ == "__main__":
    test_cases = [
        # English and Hinglish
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
        
        # Indian Languages
        ("ನನ್ನ ಬಿಲ್ ತಪ್ಪಾಗಿದೆ", "kannada"),
        ("என் பில் தவறானது", "tamil"),
        ("আমার বিল ভুল", "bengali"),
        ("నా బిల్ తప్పు", "telugu"),
        ("माझे बिल चुकीचे आहे", "marathi"),
        ("મારું બિલ ખોટું છે", "gujarati"),
        ("ਮੇਰਾ ਬਿੱਲ ਗਲਤ ਹੈ", "punjabi"),
        ("എന്റെ ബിൽ തെറ്റാണ്", "malayalam"),
        ("ମୋର ବିଲ୍ ଭୁଲ୍", "odia"),
        ("মোৰ বিল ভুল", "assamese"),
        ("میرا بل غلط ہے", "urdu"),
        ("मम गणना दोषपूर्णम् अस्ति", "sanskrit"),
        
        # International Languages
        ("Mi factura está mal", "spanish"),
        ("Ma facture est incorrecte", "french"),
        ("Meine Rechnung ist falsch", "german"),
        ("فاتورتي خاطئة", "arabic"),
        ("我的账单错了", "chinese"),
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
