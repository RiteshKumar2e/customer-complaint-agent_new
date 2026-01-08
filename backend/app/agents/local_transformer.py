"""
Local Transformer-Based Sentiment Analysis
Uses DistilBERT (lightweight BERT variant) - runs completely offline
No API quota limits, unlimited usage
"""
from transformers import pipeline
import logging

class LocalSentimentAnalyzer:
    def __init__(self):
        try:
            # DistilBERT is 40% smaller than BERT, 60% faster, retains 97% performance
            # Why? Perfect balance of speed and accuracy for production
            self.model = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # CPU mode for compatibility
            )
            logging.info("✅ Local DistilBERT Sentiment Model Loaded")
        except Exception as e:
            logging.error(f"Failed to load local sentiment model: {e}")
            self.model = None

    def analyze(self, text: str) -> dict:
        """
        Returns: {'label': 'POSITIVE'/'NEGATIVE', 'score': 0.0-1.0}
        """
        if not self.model or not text:
            return {"label": "NEUTRAL", "score": 0.5}
        
        try:
            result = self.model(text[:512])[0]  # Truncate to model limit
            
            # Map to our system's sentiment labels
            if result['label'] == 'POSITIVE':
                if result['score'] > 0.9:
                    return {"label": "Positive", "score": result['score']}
                else:
                    return {"label": "Neutral", "score": result['score']}
            else:  # NEGATIVE
                if result['score'] > 0.8:
                    return {"label": "Angry", "score": result['score']}
                elif result['score'] > 0.6:
                    return {"label": "Negative", "score": result['score']}
                else:
                    return {"label": "Neutral", "score": result['score']}
        except Exception as e:
            logging.error(f"Local sentiment analysis error: {e}")
            return {"label": "Neutral", "score": 0.5}

# Global instance
local_analyzer = LocalSentimentAnalyzer()

def get_local_sentiment(text: str) -> dict:
    return local_analyzer.analyze(text)
