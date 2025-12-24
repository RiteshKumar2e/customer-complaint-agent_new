from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from app.db.database import Base

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20), nullable=True)
    organization = Column(String(100), nullable=True)
    profile_image = Column(String(500), nullable=True)  # URL or base64 image
    hashed_password = Column(String(255), nullable=True)  # Nullable for Google/OTP users
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    otp = Column(String(255), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Complaint(Base):
    """Complaint model for storing customer complaints and AI analysis results"""
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True, nullable=True) # Professional Ticket ID (e.g. QX-12345)
    name = Column(String(100), nullable=False)  # Customer name
    email = Column(String(100), nullable=False, index=True)  # Customer email
    complaint_text = Column(Text, nullable=False)  # Original complaint
    category = Column(String(50), nullable=False)  # Billing, Technical, Delivery, Service, Security
    priority = Column(String(20), nullable=False)  # High, Medium, Low
    sentiment = Column(String(20))  # Positive, Neutral, Negative, Angry
    response = Column(Text)  # AI-generated response
    solution = Column(Text)  # Proposed solution
    satisfaction_prediction = Column(String(20))  # High, Medium, Low
    action = Column(String(255))  # Recommended action
    similar_complaints = Column(Text)  # References to similar issues
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Complaint(id={self.id}, category='{self.category}', priority='{self.priority}')>"
