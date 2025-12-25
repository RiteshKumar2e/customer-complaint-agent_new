from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from app.db.database import Base, get_ist_time

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20), nullable=True)
    organization = Column(String(100), nullable=True)
    profile_image = Column(Text, nullable=True)  # URL or base64 image
    hashed_password = Column(String(255), nullable=True)  # Nullable for Google/OTP users
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    otp = Column(String(255), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    bio = Column(Text, nullable=True)
    role = Column(String(100), default="Strategic Member")
    location = Column(String(100), default="India")
    created_at = Column(DateTime, default=get_ist_time)

class Complaint(Base):
    """Complaint model for storing customer complaints and AI analysis results"""
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True, nullable=True) # Professional Ticket ID (e.g. QX-12345)
    name = Column(String(100), nullable=False)  # Customer name
    email = Column(String(100), nullable=False, index=True)  # Customer email
    subject = Column(String(255), nullable=True) # Complaint Subject
    description = Column(Text, nullable=True)  # Detailed Complaint Description
    complaint_text = Column(Text, nullable=True) # Legacy field for DB compatibility
    category = Column(String(50), nullable=False)  # Billing, Technical, Delivery, Service, Security
    priority = Column(String(20), nullable=False)  # High, Medium, Low
    sentiment = Column(String(20))  # Positive, Neutral, Negative, Angry
    response = Column(Text)  # AI-generated response
    solution = Column(Text)  # Proposed solution
    satisfaction_prediction = Column(String(20))  # High, Medium, Low
    action = Column(String(255))  # Recommended action
    similar_complaints = Column(Text)  # References to similar issues
    ai_analysis_steps = Column(Text, nullable=True) # Stores JSON of orchestrated steps
    user_rating = Column(Integer, nullable=True) # User's review rating (1-5)
    user_feedback = Column(Text, nullable=True) # User's qualitative feedback
    created_at = Column(DateTime, default=get_ist_time, index=True)
    updated_at = Column(DateTime, default=get_ist_time, onupdate=get_ist_time)
    is_resolved = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Complaint(id={self.id}, category='{self.category}', priority='{self.priority}')>"
