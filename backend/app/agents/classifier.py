import sys
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.agents.gemini_client import async_ask_gemini

# Import LOCAL ML models (unlimited usage)
try:
    from app.agents.local_classifier import classify_local
    LOCAL_CLASSIFIER_AVAILABLE = True
except ImportError:
    LOCAL_CLASSIFIER_AVAILABLE = False

# Import training data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Training_data'))
try:
    from training_data import CLASSIFICATION_EXAMPLES, CATEGORY_KEYWORDS
except ImportError:
    CLASSIFICATION_EXAMPLES = ""
    CATEGORY_KEYWORDS = {}

def fallback_classify(text: str) -> str:
    text = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(w in text for w in keywords):
            return cat
    return "Other"

def ml_similarity_classify(text: str) -> str:
    """
    Layer 2: TF-IDF Similarity Model (Statistical ML)
    """
    categories = list(CATEGORY_KEYWORDS.keys())
    if not categories: return "Other"
    
    category_docs = [" ".join(keywords) for keywords in CATEGORY_KEYWORDS.values()]
    
    vectorizer = TfidfVectorizer().fit(category_docs + [text])
    cat_vectors = vectorizer.transform(category_docs)
    text_vector = vectorizer.transform([text])
    
    similarities = cosine_similarity(text_vector, cat_vectors).flatten()
    best_match_idx = np.argmax(similarities)
    
    if similarities[best_match_idx] > 0.15:
        return categories[best_match_idx]
    return "Other"

async def classify_complaint(text: str) -> str:
    if not text or not text.strip():
        return "Other"

    # Layer 1: Keyword-based heuristic (Instant - 0ms)
    heuristic_res = fallback_classify(text)
    if heuristic_res != "Other":
        return heuristic_res

    # Layer 2: Local BART Zero-Shot (Transformer ML - No API quota)
    # Why BART? State-of-the-art zero-shot classification, runs offline
    if LOCAL_CLASSIFIER_AVAILABLE:
        try:
            result = classify_local(text)
            if result['score'] > 0.5:  # Confidence threshold
                return result['label']
        except:
            pass

    # Layer 3: Statistical ML Similarity (Low Latency)
    ml_res = ml_similarity_classify(text)
    if ml_res != "Other":
        return ml_res

    # Layer 4: AI-based classification (High Nuance - Contextual LLM)
    prompt = f"""
{CLASSIFICATION_EXAMPLES}

Classify this complaint into ONE category only:
Billing, Technical, Delivery, Service, Security, Other

Complaint:
{text}

Return only the category name.
"""
    try:
        result = await async_ask_gemini(prompt)
        allowed = {"Billing", "Technical", "Delivery", "Service", "Security", "Other"}
        filtered_res = result.strip().split('\n')[0].replace('.', '').strip()
        return filtered_res if filtered_res in allowed else fallback_classify(text)
    except Exception:
        return fallback_classify(text)
