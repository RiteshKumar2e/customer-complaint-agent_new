import re
from typing import Dict, Tuple

# ========================================
# RESPONSE VALIDATION & QUALITY CHECKS
# ========================================
# Ensures responses meet accuracy and quality standards

VALID_CATEGORIES = {"Billing", "Technical", "Delivery", "Service", "Security", "Other"}
VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_SENTIMENTS = {"Positive", "Neutral", "Negative", "Angry"}
VALID_SATISFACTION = {"Low", "Medium", "High"}

MIN_RESPONSE_LENGTH = 10  # Minimum characters
MAX_RESPONSE_LENGTH = 500  # Maximum characters


class ResponseValidator:
    """Validates and scores response quality"""
    
    @staticmethod
    def validate_category(category: str) -> Tuple[bool, str]:
        """Validate category value"""
        category = category.strip()
        if category in VALID_CATEGORIES:
            return True, category
        # Find closest match
        closest = ResponseValidator._find_closest_match(category, VALID_CATEGORIES)
        return False, closest
    
    @staticmethod
    def validate_priority(priority: str) -> Tuple[bool, str]:
        """Validate priority value"""
        priority = priority.strip()
        if priority in VALID_PRIORITIES:
            return True, priority
        closest = ResponseValidator._find_closest_match(priority, VALID_PRIORITIES)
        return False, closest
    
    @staticmethod
    def validate_sentiment(sentiment: str) -> Tuple[bool, str]:
        """Validate sentiment value"""
        sentiment = sentiment.strip()
        if sentiment in VALID_SENTIMENTS:
            return True, sentiment
        closest = ResponseValidator._find_closest_match(sentiment, VALID_SENTIMENTS)
        return False, closest
    
    @staticmethod
    def validate_response_text(text: str) -> Tuple[bool, str, float]:
        """
        Validate response text quality
        Returns: (is_valid, cleaned_text, confidence_score)
        """
        if not text or not text.strip():
            return False, "Unable to generate response", 0.0
        
        text = text.strip()
        
        # Length check
        if len(text) < MIN_RESPONSE_LENGTH:
            return False, "Response too short", 0.3
        
        if len(text) > MAX_RESPONSE_LENGTH:
            # Truncate long responses
            text = text[:MAX_RESPONSE_LENGTH] + "..."
        
        # Quality score based on characteristics
        score = ResponseValidator._calculate_quality_score(text)
        
        is_valid = score >= 0.5 and len(text) >= MIN_RESPONSE_LENGTH
        return is_valid, text, score
    
    @staticmethod
    def _calculate_quality_score(text: str) -> float:
        """Calculate response quality score (0-1)"""
        score = 0.0
        max_score = 5.0
        
        # Professionalism (proper sentences)
        if re.search(r'[.!?]\s+[A-Z]', text) or text.endswith(('.', '!', '?')):
            score += 1.0
        
        # Length (optimal 50-300 chars)
        if 50 <= len(text) <= 300:
            score += 1.0
        
        # Empathy words
        empathy_words = ['appreciate', 'understand', 'sorry', 'help', 'thank', 'please']
        if any(word in text.lower() for word in empathy_words):
            score += 1.0
        
        # Action-oriented
        action_words = ['will', 'investigate', 'review', 'contact', 'process', 'resolve']
        if any(word in text.lower() for word in action_words):
            score += 1.0
        
        # No spam/gibberish (reasonable character diversity)
        unique_chars = len(set(text))
        if unique_chars > 20:
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    @staticmethod
    def _find_closest_match(text: str, options: set) -> str:
        """Find closest matching option using simple similarity"""
        text_lower = text.lower()
        for option in options:
            if text_lower in option.lower() or option.lower() in text_lower:
                return option
        return list(options)[0] if options else "Other"
    
    @staticmethod
    def validate_full_response(response: dict) -> Tuple[bool, dict]:
        """Validate complete complaint response"""
        errors = []
        
        # Validate required fields
        if not response.get("category"):
            errors.append("Missing category")
        else:
            is_valid, fixed = ResponseValidator.validate_category(response["category"])
            response["category"] = fixed
        
        if not response.get("priority"):
            errors.append("Missing priority")
        else:
            is_valid, fixed = ResponseValidator.validate_priority(response["priority"])
            response["priority"] = fixed
        
        if not response.get("response"):
            errors.append("Missing response text")
        else:
            is_valid, text, score = ResponseValidator.validate_response_text(response["response"])
            response["response"] = text
            response["response_quality"] = score
        
        if not response.get("action"):
            response["action"] = "Escalate to support team"
        
        # Validate optional fields
        if response.get("sentiment"):
            is_valid, fixed = ResponseValidator.validate_sentiment(response["sentiment"])
            response["sentiment"] = fixed
        else:
            response["sentiment"] = "Neutral"
        
        response["validation_errors"] = errors
        is_valid = len(errors) == 0
        
        return is_valid, response


class AccuracyMonitor:
    """Tracks chatbot accuracy metrics"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_responses = 0
        self.cached_responses = 0
        self.fallback_used = 0
        self.validation_failures = 0
    
    def record_success(self, from_cache: bool = False):
        """Record successful response"""
        self.total_requests += 1
        self.successful_responses += 1
        if from_cache:
            self.cached_responses += 1
    
    def record_fallback(self):
        """Record fallback usage"""
        self.total_requests += 1
        self.fallback_used += 1
    
    def record_validation_failure(self):
        """Record validation failure"""
        self.validation_failures += 1
    
    def get_accuracy_metrics(self) -> dict:
        """Get accuracy metrics"""
        if self.total_requests == 0:
            return {
                "success_rate": "0%",
                "cache_hit_rate": "0%",
                "fallback_rate": "0%"
            }
        
        success_rate = (self.successful_responses / self.total_requests * 100)
        cache_hit_rate = (self.cached_responses / self.total_requests * 100)
        fallback_rate = (self.fallback_used / self.total_requests * 100)
        
        return {
            "total_requests": self.total_requests,
            "success_rate": f"{success_rate:.2f}%",
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "fallback_rate": f"{fallback_rate:.2f}%",
            "validation_failures": self.validation_failures
        }


accuracy_monitor = AccuracyMonitor()