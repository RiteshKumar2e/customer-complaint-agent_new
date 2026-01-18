import numpy as np
from sklearn.linear_model import LogisticRegression
from typing import Dict

class ChurnPredictor:
    """
    ML model to predict Customer Churn Risk based on complaint tone and history.
    Uses a Logistic Regression classifier on sentiment features.
    """
    def __init__(self):
        self.model = LogisticRegression()
        # Training data: [sentiment_score, urgency_score, previous_complaints_count]
        # sentiment_score: -1 (very negative) to 1 (very positive)
        # urgency_score: 0 to 1
        X_train = np.array([
            [-0.8, 0.9, 5], [-0.9, 1.0, 8], [-0.5, 0.6, 2], [0.1, 0.2, 0],
            [0.5, 0.1, 1], [-0.2, 0.4, 3], [-0.7, 0.8, 4], [0.8, 0.0, 0]
        ])
        # labels: 1 (High Churn Risk), 0 (Low Risk)
        y_train = np.array([1, 1, 0, 0, 0, 0, 1, 0])
        self.model.fit(X_train, y_train)

    def predict_risk(self, sentiment: str, text: str) -> str:
        """
        Calculates churn risk probability.
        """
        # Feature Extraction
        sentiment_map = {"Angry": -0.9, "Negative": -0.6, "Neutral": 0.0, "Positive": 0.6}
        sentiment_score = sentiment_map.get(sentiment, 0.0)
        
        urgency_score = 0.8 if any(word in text.lower() for word in ['urgent', 'immediately', 'now', 'stop', 'lawyer', 'refund']) else 0.2
        
        # In a real app, we'd pull the actual count from the DB
        # For demo, we estimate based on text complexity
        prev_count_est = min(len(text) // 100, 10) 
        
        features = np.array([[sentiment_score, urgency_score, prev_count_est]])
        prob = self.model.predict_proba(features)[0][1]
        
        if prob > 0.7: return "Critical"
        if prob > 0.4: return "Elevated"
        return "Low"

churn_agent = ChurnPredictor()

async def predict_churn_risk(sentiment: str, text: str):
    return churn_agent.predict_risk(sentiment, text)
