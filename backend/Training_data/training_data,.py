# ========================================
# TRAINING DATA FOR CHATBOT
# ========================================
# This module contains training examples and patterns
# to improve accuracy and speed of the complaint classification

COMPLAINT_EXAMPLES = {
    "Billing": [
        {
            "text": "I was charged $50 twice for the same order. I need an immediate refund!",
            "priority": "High",
            "sentiment": "Angry",
            "solution": "Review billing records and process refund"
        },
        {
            "text": "My bill seems higher than expected this month. Can you review it?",
            "priority": "Medium",
            "sentiment": "Negative",
            "solution": "Check billing calculation and explain charges"
        },
        {
            "text": "I want to understand the subscription charges better.",
            "priority": "Low",
            "sentiment": "Neutral",
            "solution": "Provide detailed billing breakdown"
        }
    ],
    "Technical": [
        {
            "text": "The website keeps crashing when I try to login! I've tried 10 times.",
            "priority": "High",
            "sentiment": "Angry",
            "solution": "Investigate login functionality and deploy fix"
        },
        {
            "text": "The app is running very slowly on my phone.",
            "priority": "Medium",
            "sentiment": "Negative",
            "solution": "Check for performance issues and optimize"
        },
        {
            "text": "I noticed a small typo in the dashboard.",
            "priority": "Low",
            "sentiment": "Neutral",
            "solution": "Fix UI text in next release"
        }
    ],
    "Delivery": [
        {
            "text": "My order was supposed to arrive 5 days ago! Where is it? This is unacceptable!",
            "priority": "High",
            "sentiment": "Angry",
            "solution": "Trace shipment and expedite or send replacement"
        },
        {
            "text": "Package arrived damaged. The product inside is broken.",
            "priority": "High",
            "sentiment": "Negative",
            "solution": "Issue replacement and arrange return"
        },
        {
            "text": "When will my order be delivered?",
            "priority": "Low",
            "sentiment": "Neutral",
            "solution": "Provide tracking information"
        }
    ],
    "Service": [
        {
            "text": "The support team was incredibly rude to me! I will never come back.",
            "priority": "High",
            "sentiment": "Angry",
            "solution": "Apologize and have supervisor contact customer"
        },
        {
            "text": "I've been waiting 2 weeks for a response to my email.",
            "priority": "Medium",
            "sentiment": "Frustrated",
            "solution": "Escalate to senior support team"
        },
        {
            "text": "Can you help me with my account settings?",
            "priority": "Low",
            "sentiment": "Neutral",
            "solution": "Provide step-by-step guidance"
        }
    ],
    "Security": [
        {
            "text": "I think my account has been hacked! Someone made fraudulent purchases!",
            "priority": "High",
            "sentiment": "Angry",
            "solution": "Secure account, reverse charges, enable 2FA"
        },
        {
            "text": "I noticed suspicious login activity from a different country.",
            "priority": "High",
            "sentiment": "Concerned",
            "solution": "Reset password, review activity, enable alerts"
        },
        {
            "text": "Is my payment information secure on your platform?",
            "priority": "Medium",
            "sentiment": "Neutral",
            "solution": "Explain security measures and certifications"
        }
    ]
}

PRIORITY_KEYWORDS = {
    "High": [
        "urgent", "immediately", "angry", "furious", "refund", "fraud", "scam", 
        "charged", "not working", "failed", "security", "breach", "harassment", 
        "threat", "critical", "emergency", "unacceptable", "outrageous", "worst"
    ],
    "Medium": [
        "delay", "late", "problem", "issue", "slow", "pending", "confused", 
        "not received", "waiting", "frustrated", "concern", "help needed"
    ],
    "Low": [
        "question", "inquiry", "how", "when", "where", "minor", "typo", "info"
    ]
}

SENTIMENT_KEYWORDS = {
    "Angry": [
        "worst", "terrible", "disgusting", "unacceptable", "furious", 
        "extremely angry", "outrageous", "scam", "fraud", "lie", "never"
    ],
    "Negative": [
        "bad", "poor", "disappointed", "unhappy", "frustrated", "upset", 
        "angry", "issue", "problem", "complaint", "failed", "broken"
    ],
    "Positive": [
        "good", "great", "excellent", "thanks", "appreciate", "thank you", 
        "helpful", "resolved", "satisfied", "happy", "awesome"
    ],
    "Neutral": []
}

CATEGORY_KEYWORDS = {
    "Billing": ["refund", "payment", "bill", "charge", "invoice", "subscription", "cost", "price"],
    "Technical": ["error", "bug", "crash", "login", "website", "app", "slow", "not working"],
    "Delivery": ["delivery", "delay", "shipment", "late", "package", "arrived", "tracking"],
    "Service": ["support", "staff", "rude", "service", "team", "help", "contact"],
    "Security": ["fraud", "hack", "security", "breach", "account", "suspicious", "scam"]
}

# Few-shot examples for Gemini prompts
CLASSIFICATION_EXAMPLES = """
Examples:
- "My payment didn't go through" → Billing
- "The login page shows an error" → Technical
- "My package hasn't arrived in 10 days" → Delivery
- "Customer support was unhelpful" → Service
- "Someone accessed my account" → Security
"""

SENTIMENT_EXAMPLES = """
Examples:
- "I'm absolutely furious about this" → Angry
- "This is disappointing" → Negative
- "Thank you for your help" → Positive
- "Can you provide information?" → Neutral
"""

SOLUTION_EXAMPLES = """
Examples:
- Billing issue → Check records and process refund/adjustment
- Technical issue → Investigate and provide fix or workaround
- Delivery issue → Trace shipment and expedite or send replacement
- Service issue → Escalate to senior team member
- Security issue → Secure account and provide monitoring
"""

# Response templates for faster generation
RESPONSE_TEMPLATES = {
    "Billing": {
        "High": "Thank you for bringing this billing issue to our attention. We take this seriously and will investigate your charges immediately and contact you within 24 hours.",
        "Medium": "We understand your concern about billing. Our finance team will review your account and provide a detailed explanation.",
        "Low": "We appreciate you reaching out. We'll be happy to clarify any charges on your account."
    },
    "Technical": {
        "High": "We sincerely apologize for the technical difficulty you're experiencing. Our engineers are treating this as a priority and working on a fix.",
        "Medium": "Thank you for reporting this technical issue. Our team is investigating and will have an update for you soon.",
        "Low": "We appreciate you pointing out this technical issue. We'll include this in our next release."
    },
    "Delivery": {
        "High": "We sincerely apologize for the delivery delay. We're actively tracking your package and will update you immediately.",
        "Medium": "Thank you for your patience. We're tracking your shipment and will ensure timely delivery.",
        "Low": "Thank you for your inquiry. We'll provide you with the latest tracking information."
    },
    "Service": {
        "High": "We're truly sorry for the poor service experience. A senior team member will contact you personally to make this right.",
        "Medium": "We appreciate your feedback about our service. We'll escalate this to our supervisor.",
        "Low": "Thank you for your feedback. Our team is here to help."
    },
    "Security": {
        "High": "Your security concern is critical to us. Our security team is investigating immediately and will secure your account.",
        "Medium": "Your account security is important. We're reviewing this and will take appropriate protective measures.",
        "Low": "Thank you for your security question. We maintain industry-standard protections."
    }
}