from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ComplaintRequest(BaseModel):
    """Request schema for submitting a complaint"""
    name: str
    email: str
    complaint: str


class ComplaintResponse(BaseModel):
    """Response schema with AI analysis results"""
    ticket_id: Optional[str] = None
    category: str
    priority: str
    response: str
    action: str
    sentiment: str
    solution: str
    satisfaction: str
    similar_issues: str
    steps: Optional[list] = None


class ComplaintDB(BaseModel):
    """Database schema for storing complaint"""
    id: int
    ticket_id: Optional[str] = None
    complaint_text: str
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