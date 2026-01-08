import numpy as np
from sklearn.ensemble import IsolationForest
import logging

class AnomalyDetector:
    """
    Advanced ML Anomaly Detection Agent.
    Uses Isolation Forest (Unsupervised DL/ML) to detect if a complaint 
    is an outlier compared to historical patterns (e.g., potential DDoS or bot-spam).
    """
    def __init__(self):
        self.model = IsolationForest(contamination=0.05, random_state=42)
        # Mock historical data features [length, special_chars_count, word_entropy]
        self.history = np.array([
            [100, 5, 4.5], [150, 10, 4.8], [200, 15, 5.0], [80, 2, 4.2],
            [300, 20, 5.2], [120, 6, 4.6], [180, 12, 4.9], [250, 18, 5.1]
        ])
        self.model.fit(self.history)

    def is_anomaly(self, text: str) -> bool:
        """
        Predicts if the current complaint is a structural anomaly.
        """
        try:
            length = len(text)
            special_chars = sum(1 for char in text if not char.isalnum())
            words = text.split()
            word_len = [len(w) for w in words]
            entropy = np.std(word_len) if word_len else 0
            
            features = np.array([[length, special_chars, entropy]])
            prediction = self.model.predict(features)
            
            # -1 means anomaly, 1 means normal
            return prediction[0] == -1
        except Exception as e:
            logging.error(f"Anomaly detection error: {e}")
            return False

detector = AnomalyDetector()

async def check_anomaly(text: str):
    return detector.is_anomaly(text)
