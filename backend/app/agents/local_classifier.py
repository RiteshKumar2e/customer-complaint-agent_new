"""
Zero-Shot Classification using Facebook's BART
Completely local, no API calls, unlimited usage
Perfect for categorizing complaints without training data
"""
from transformers import pipeline
import logging

class LocalZeroShotClassifier:
    def __init__(self):
        try:
            # Facebook's BART-large-mnli: State-of-the-art zero-shot classification
            # Why? Can classify into ANY category without training
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1
            )
            logging.info("✅ Local BART Zero-Shot Classifier Loaded")
        except Exception as e:
            logging.error(f"Failed to load zero-shot classifier: {e}")
            self.classifier = None

    def classify(self, text: str, categories: list) -> dict:
        """
        Classifies text into one of the given categories
        Returns: {'label': 'category_name', 'score': confidence}
        """
        if not self.classifier or not text or not categories:
            return {"label": "Other", "score": 0.0}
        
        try:
            result = self.classifier(
                text[:512],
                candidate_labels=categories,
                multi_label=False
            )
            
            return {
                "label": result['labels'][0],
                "score": result['scores'][0]
            }
        except Exception as e:
            logging.error(f"Zero-shot classification error: {e}")
            return {"label": "Other", "score": 0.0}

# Global instance
local_classifier = LocalZeroShotClassifier()

def classify_local(text: str, categories: list = None) -> dict:
    if categories is None:
        categories = ["Billing", "Technical", "Delivery", "Service", "Security", "Other"]
    return local_classifier.classify(text, categories)
