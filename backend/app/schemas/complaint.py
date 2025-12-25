from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ComplaintRequest(BaseModel):
    """Request schema for submitting a complaint"""
    name: Optional[str] = ""
    email: Optional[str] = ""
    subject: Optional[str] = ""
    description: Optional[str] = ""
    category: Optional[str] = "Other"


class ComplaintResponse(BaseModel):
    """Response schema with AI analysis results"""
    ticket_id: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "Other"
    priority: Optional[str] = "Low"
    response: Optional[str] = ""
    action: Optional[str] = ""
    sentiment: Optional[str] = "Neutral"
    solution: Optional[str] = ""
    satisfaction: Optional[str] = "Medium"
    similar_issues: Optional[str] = ""
    steps: Optional[list] = []


class ComplaintDB(BaseModel):
    """Database schema for storing complaint"""
    id: int
    ticket_id: Optional[str] = None
    subject: Optional[str] = None
    description: str
    category: str
    priority: str
    sentiment: Optional[str]
    response: Optional[str]
    solution: Optional[str]
    satisfaction_prediction: Optional[str]
    action: Optional[str]
    similar_complaints: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_resolved: bool

    class Config:
        from_attributes = True