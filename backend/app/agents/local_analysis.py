"""
Deterministic, offline complaint analysis.

Used when no LLM provider answers (or answers with invalid output), so a
complaint is never lost or stored with garbage. It is intentionally simple:
whole-word keyword rules from Training_data, a TF-IDF similarity fallback for
category, keyword + TextBlob polarity for sentiment, and template text. Results
from this path are always marked `fallback_used` and sent for human review.
"""
from __future__ import annotations

import os
import sys
from typing import Dict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.agents.keywords import contains_keyword

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "Training_data"))
try:  # pragma: no cover - import guard
    from training_data import CATEGORY_KEYWORDS, PRIORITY_KEYWORDS, SENTIMENT_KEYWORDS
except ImportError:  # pragma: no cover
    CATEGORY_KEYWORDS, PRIORITY_KEYWORDS, SENTIMENT_KEYWORDS = {}, {}, {}

LOCAL_MODEL_NAME = "keyword-tfidf-v1"

CATEGORY_RESPONSES = {
    "Billing": {
        "english": "Thank you for contacting us about your billing concern. Our billing team will review your account and get back to you.",
        "hinglish": "Aapki billing concern ke liye dhanyavaad. Humari billing team aapke account ko review karke aapse sampark karegi.",
        "hindi": "आपकी बिलिंग समस्या के लिए धन्यवाद। हमारी बिलिंग टीम आपके खाते की समीक्षा करके आपसे संपर्क करेगी।",
    },
    "Technical": {
        "english": "Thank you for reporting this technical issue. Our technical team is investigating and will update you.",
        "hinglish": "Technical issue report karne ke liye shukriya. Humari team investigate karke aapko update karegi.",
        "hindi": "तकनीकी समस्या की रिपोर्ट के लिए धन्यवाद। हमारी टीम जांच करके आपको अपडेट करेगी।",
    },
    "Delivery": {
        "english": "We are sorry about the trouble with your delivery. We are checking the shipment status and will update you.",
        "hinglish": "Delivery ki problem ke liye maafi. Hum shipment status check karke aapko update karenge.",
        "hindi": "डिलीवरी की समस्या के लिए खेद है। हम शिपमेंट की स्थिति जांचकर आपको अपडेट करेंगे।",
    },
    "Service": {
        "english": "Thank you for telling us about your experience. A member of our support team will follow up with you.",
        "hinglish": "Apna experience batane ke liye dhanyavaad. Humari support team aapse follow up karegi.",
        "hindi": "अपना अनुभव बताने के लिए धन्यवाद। हमारी सहायता टीम आपसे संपर्क करेगी।",
    },
    "Security": {
        "english": "Thank you for reporting this security concern. Our team is reviewing it as a priority. Please change your password and do not share any codes with anyone.",
        "hinglish": "Security concern report karne ke liye dhanyavaad. Team ise priority par dekh rahi hai. Kripya apna password badal lein aur kisi ke saath code share na karein.",
        "hindi": "सुरक्षा समस्या की रिपोर्ट के लिए धन्यवाद। टीम इसे प्राथमिकता से देख रही है। कृपया अपना पासवर्ड बदलें और किसी के साथ कोड साझा न करें।",
    },
    "Other": {
        "english": "Thank you for contacting us. Our support team is reviewing your request and will respond soon.",
        "hinglish": "Contact karne ke liye dhanyavaad. Humari support team aapki request review kar rahi hai.",
        "hindi": "संपर्क करने के लिए धन्यवाद। हमारी सहायता टीम आपके अनुरोध की समीक्षा कर रही है।",
    },
}

CATEGORY_SOLUTIONS = {
    "Billing": "1. Our billing team will verify the charges on your account.\n2. If an incorrect charge is confirmed, it will be reversed according to our refund policy.\n3. You will receive an update on this ticket once the review is complete.",
    "Technical": "1. Our technical team will try to reproduce the issue you described.\n2. Meanwhile, try clearing your browser cache or updating the app.\n3. We will update this ticket with a fix or workaround.",
    "Delivery": "1. We will check the latest tracking status with the courier.\n2. If the shipment is delayed or lost, we will arrange the next step (re-dispatch or refund) as per policy.\n3. You will get an update on this ticket.",
    "Service": "1. A support lead will review your experience.\n2. They will contact you to understand what went wrong.\n3. We will share the outcome on this ticket.",
    "Security": "1. Change your account password immediately.\n2. Do not share OTPs or passwords with anyone.\n3. Our security team will review recent activity on your account and update this ticket.",
    "Other": "1. Our support team will review your request.\n2. We may contact you for more details.\n3. You will receive an update on this ticket.",
}

_categories = list(CATEGORY_KEYWORDS.keys())
_vectorizer = None
_category_matrix = None
if _categories:
    _vectorizer = TfidfVectorizer().fit([" ".join(k) for k in CATEGORY_KEYWORDS.values()])
    _category_matrix = _vectorizer.transform([" ".join(k) for k in CATEGORY_KEYWORDS.values()])


def classify_category(text: str) -> str:
    lowered = (text or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if contains_keyword(lowered, keywords):
            return category
    if _vectorizer is not None and lowered.strip():
        similarities = cosine_similarity(_vectorizer.transform([lowered]), _category_matrix).flatten()
        best = int(np.argmax(similarities))
        if similarities[best] > 0.15:
            return _categories[best]
    return "Other"


def detect_priority(text: str) -> str:
    lowered = (text or "").lower()
    if contains_keyword(lowered, PRIORITY_KEYWORDS.get("High", [])):
        return "High"
    if contains_keyword(lowered, PRIORITY_KEYWORDS.get("Medium", [])):
        return "Medium"
    return "Low"


def detect_sentiment(text: str) -> str:
    lowered = (text or "").lower()
    for sentiment in ("Angry", "Negative", "Positive"):
        if contains_keyword(lowered, SENTIMENT_KEYWORDS.get(sentiment, [])):
            return sentiment
    try:
        from textblob import TextBlob

        polarity = TextBlob(text).sentiment.polarity
        if polarity > 0.5:
            return "Positive"
        if polarity < -0.6:
            return "Angry"
        if polarity < -0.1:
            return "Negative"
    except Exception:
        pass
    return "Neutral"


def _lang_key(language: str) -> str:
    return language if language in ("english", "hinglish", "hindi") else "english"


def fallback_response(category: str, language: str = "english") -> str:
    return CATEGORY_RESPONSES.get(category, CATEGORY_RESPONSES["Other"])[_lang_key(language)]


def fallback_solution(category: str) -> str:
    return CATEGORY_SOLUTIONS.get(category, CATEGORY_SOLUTIONS["Other"])


def analyze(text: str, language: str = "english") -> Dict[str, str]:
    category = classify_category(text)
    priority = detect_priority(text)
    if category == "Security" and priority == "Low":
        priority = "Medium"
    sentiment = detect_sentiment(text)
    return {
        "category": category,
        "priority": priority,
        "sentiment": sentiment,
        "satisfaction": "Low" if sentiment in ("Angry",) else "Medium",
        "response": fallback_response(category, language),
        "solution": fallback_solution(category),
    }
