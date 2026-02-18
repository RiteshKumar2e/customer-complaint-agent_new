from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON
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
    is_agent = Column(Boolean, default=False)  # Agent Module access
    bio = Column(Text, nullable=True)
    role = Column(String(100), default="Strategic Member")
    location = Column(String(100), default="India")
    created_at = Column(DateTime, default=get_ist_time)

class LoginHistory(Base):
    """Login history model for tracking user login attempts"""
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    user_name = Column(String(100), nullable=True) # User's full name
    email = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True) # User's phone number
    login_method = Column(String(50), nullable=False)  # 'password', 'otp', 'google'
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)  # Browser info
    device_type = Column(String(100), nullable=True) # Mobile, Tablet, Desktop
    login_location = Column(String(255), nullable=True) # City, Country (Approximate)
    success = Column(Boolean, default=True)  # Login successful or failed
    status = Column(String(50), default="Completed") # Login Status
    failure_reason = Column(String(255), nullable=True)  # Reason if failed
    login_time = Column(DateTime, default=get_ist_time, index=True)
    logout_time = Column(DateTime, nullable=True) # Time when user logged out
    created_at = Column(DateTime, default=get_ist_time)
    
    def __repr__(self):
        return f"<LoginHistory(user_id={self.user_id}, email='{self.email}', method='{self.login_method}', time='{self.login_time}')>"

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
    sentiment_score = Column(Float, default=0.0) # Numerical sentiment score
    response = Column(Text)  # AI-generated response
    solution = Column(Text)  # Proposed solution
    satisfaction_prediction = Column(String(20))  # High, Medium, Low
    action = Column(String(255))  # Recommended action
    similar_complaints = Column(Text)  # References to similar issues
    ai_analysis_steps = Column(Text, nullable=True) # Stores JSON of orchestrated steps
    user_rating = Column(Integer, nullable=True) # User's review rating (1-5)
    user_feedback = Column(Text, nullable=True) # User's qualitative feedback
    user_resolution_feedback = Column(Boolean, nullable=True) # User's feedback on whether complaint was actually resolved
    user_resolution_comment = Column(Text, nullable=True) # User's comment about resolution status
    created_at = Column(DateTime, default=get_ist_time, index=True)
    updated_at = Column(DateTime, default=get_ist_time, onupdate=get_ist_time)
    is_resolved = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Complaint(id={self.id}, category='{self.category}', priority='{self.priority}')>"

class AgentResolution(Base):
    """Agent Resolution model for storing human-verified solutions with multi-model validation"""
    __tablename__ = "agent_resolutions"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey('complaints.id'), nullable=False, index=True)
    ticket_id = Column(String(50), index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    
    # Solution content
    draft_solution = Column(Text, nullable=True)  # Initial draft by agent
    final_solution = Column(Text, nullable=False)  # Final verified solution
    
    # Validation data
    validation_results = Column(JSON, nullable=True)  # Stores multi-model validation data
    confidence_score = Column(Float, nullable=True)  # Average confidence from all models (0-1)
    validation_status = Column(String(50), default="pending")  # pending, approved, rejected, needs_revision
    model_agreement_metrics = Column(JSON, nullable=True)  # Detailed model consensus data
    
    # Status and timestamps
    resolution_timestamp = Column(DateTime, nullable=True)  # When resolution was sent
    status = Column(String(50), default="draft")  # draft, validated, sent, delivered
    created_at = Column(DateTime, default=get_ist_time, index=True)
    updated_at = Column(DateTime, default=get_ist_time, onupdate=get_ist_time)
    
    def __repr__(self):
        return f"<AgentResolution(id={self.id}, ticket_id='{self.ticket_id}', status='{self.status}')>"

class ModelValidation(Base):
    """Model Validation results for individual AI model assessments"""
    __tablename__ = "model_validations"

    id = Column(Integer, primary_key=True, index=True)
    resolution_id = Column(Integer, ForeignKey('agent_resolutions.id'), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)  # e.g., "llama-3.3-70b-versatile"
    
    # Validation criteria
    validation_type = Column(String(50), nullable=False)  # correctness, completeness, safety, actionability, clarity
    score = Column(Float, nullable=False)  # 0-1 score for this criterion
    feedback = Column(Text, nullable=True)  # Model's feedback/suggestions
    passed = Column(Boolean, default=False)  # Whether this criterion passed threshold
    
    created_at = Column(DateTime, default=get_ist_time)
    
    def __repr__(self):
        return f"<ModelValidation(model='{self.model_name}', type='{self.validation_type}', score={self.score})>"

class AgentAuditLog(Base):
    """Audit log for tracking all agent actions in the system"""
    __tablename__ = "agent_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # view_complaint, draft_solution, submit_validation, send_resolution
    
    # Complaint reference
    complaint_id = Column(Integer, nullable=True)
    ticket_id = Column(String(50), nullable=True, index=True)
    
    # Audit details
    details = Column(JSON, nullable=True)  # Additional action-specific data
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=get_ist_time, index=True)
    
    def __repr__(self):
        return f"<AgentAuditLog(agent_id={self.agent_id}, action='{self.action}', time='{self.timestamp}')>"
