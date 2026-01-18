from textblob import TextBlob
import re

class UrgencyModel:
    """
    ML agent to detect the intensity of urgency and emotional distress.
    Uses NLP heuristics and sentiment intensity.
    """
    def analyze_urgency(self, text: str) -> Dict:
        """
        Returns urgency score (0-100) and specific flags.
        """
        text_lower = text.lower()
        score = 0
        flags = []
        
        # Keyword based urgency
        critical_words = {
            'asap': 15, 'immediately': 20, 'urgent': 20, 'emergency': 30,
            'now': 10, 'broken': 15, 'stolen': 35, 'hacked': 40,
            'police': 30, 'lawyer': 25, 'sue': 25, 'legal': 20
        }
        
        for word, weight in critical_words.items():
            if word in text_lower:
                score += weight
                flags.append(word.capitalize())
        
        # Punctuation and style
        if '!' in text: score += 10
        if text.isupper() and len(text) > 10: score += 20
        
        # Sentiment intensity (using TextBlob)
        blob = TextBlob(text)
        sentiment_polarity = blob.sentiment.polarity
        if sentiment_polarity < -0.5:
            score += 20
            flags.append("High Distress")
            
        # Cap at 100
        final_score = min(score, 100)
        
        intensity = "Low"
        if final_score > 70: intensity = "Critical"
        elif final_score > 40: intensity = "Medium"
        
        return {
            "urgency_score": final_score,
            "intensity": intensity,
            "flags": flags[:3] # Top 3 flags
        }

from typing import Dict
urgency_analyzer = UrgencyModel()

async def analyze_complaint_urgency(text: str):
    return urgency_analyzer.analyze_urgency(text)
