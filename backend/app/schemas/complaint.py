"""Complaint request/response schemas."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validators import clean_text

Status = Literal["open", "in_progress", "awaiting_approval", "resolved", "closed"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ComplaintRequest(BaseModel):
    """
    New complaint. Name and email always come from the signed-in account; the
    optional fields are accepted (and ignored) for compatibility with older clients.
    """

    model_config = ConfigDict(extra="ignore")

    subject: str
    description: str
    category: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None

    @field_validator("subject", mode="before")
    @classmethod
    def _subject(cls, v):
        text = clean_text(v, 200, "Subject", required=True)
        if len(text) < 5:
            raise ValueError("Subject must be at least 5 characters")
        return text

    @field_validator("description", mode="before")
    @classmethod
    def _description(cls, v):
        text = clean_text(v, 5000, "Description", required=True)
        if len(text) < 20:
            raise ValueError("Please describe the problem in at least 20 characters")
        return text


class ReviewRequest(Strict):
    rating: int = Field(ge=1, le=5)
    feedback: Optional[str] = None

    @field_validator("feedback", mode="before")
    @classmethod
    def _fb(cls, v):
        return clean_text(v, 2000, "Feedback")


class ResolutionFeedbackRequest(Strict):
    is_actually_resolved: bool
    user_comment: Optional[str] = ""

    @field_validator("user_comment", mode="before")
    @classmethod
    def _c(cls, v):
        return clean_text(v, 2000, "Comment") or ""


class StatusUpdateRequest(Strict):
    status: Optional[Status] = None
    is_resolved: Optional[bool] = None  # legacy clients
    note: Optional[str] = None
    admin_solution: Optional[str] = None

    @field_validator("note", "admin_solution", mode="before")
    @classmethod
    def _t(cls, v):
        return clean_text(v, 4000, "Text")


class AssignRequest(Strict):
    agent_id: Optional[int] = None


class NoteRequest(Strict):
    note: str
    internal: bool = True

    @field_validator("note", mode="before")
    @classmethod
    def _n(cls, v):
        return clean_text(v, 4000, "Note", required=True)


class BulkDeleteRequest(Strict):
    ids: List[int] = Field(min_length=1, max_length=200)


class ResolutionRequest(BaseModel):
    """Agent resolution body. `agent_email` from old clients is ignored: identity comes from the token."""

    model_config = ConfigDict(extra="ignore")

    ticket_id: str = Field(min_length=3, max_length=50)
    solution: Optional[str] = None
    draft_solution: Optional[str] = None
    final_solution: Optional[str] = None
    steps: Optional[List[Any]] = None

    def text(self) -> str:
        value = self.final_solution or self.draft_solution or self.solution or ""
        cleaned = clean_text(value, 6000, "Solution", required=True)
        if len(cleaned) < 10:
            raise ValueError("Solution must be at least 10 characters")
        return cleaned


def _steps(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (TypeError, ValueError):
        return []


class ComplaintOut(BaseModel):
    """Fields every authorised viewer (including the customer) may see."""

    id: int
    ticket_id: Optional[str]
    name: str
    email: str
    subject: Optional[str]
    description: Optional[str]
    category: str
    priority: str
    sentiment: Optional[str]
    status: str
    is_resolved: bool
    response: Optional[str]
    solution: Optional[str]
    action: Optional[str]
    satisfaction_prediction: Optional[str]
    similar_complaints: Optional[str]
    steps: list = []
    user_rating: Optional[int]
    user_feedback: Optional[str]
    user_resolution_feedback: Optional[bool]
    user_resolution_comment: Optional[str]
    assigned_agent_name: Optional[str] = None
    attachment_count: int = 0
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]


class StaffComplaintOut(ComplaintOut):
    """Adds internal triage and AI provenance for agents and admins."""

    user_id: Optional[int]
    assigned_agent_id: Optional[int]
    assigned_at: Optional[datetime]
    requires_human_review: bool
    review_reason: Optional[str]
    ai_provider: Optional[str]
    ai_model: Optional[str]
    ai_latency_ms: Optional[int]
    ai_fallback_used: bool


def complaint_to_dict(c, staff: bool, agent_name: Optional[str] = None, attachment_count: int = 0) -> dict:
    base = dict(
        id=c.id, ticket_id=c.ticket_id, name=c.name, email=c.email, subject=c.subject,
        description=c.description or c.complaint_text, category=c.category, priority=c.priority,
        sentiment=c.sentiment, status=c.status or ("resolved" if c.is_resolved else "open"),
        is_resolved=bool(c.is_resolved), response=c.response, solution=c.solution, action=c.action,
        satisfaction_prediction=c.satisfaction_prediction, similar_complaints=c.similar_complaints,
        steps=_steps(c.ai_analysis_steps), user_rating=c.user_rating, user_feedback=c.user_feedback,
        user_resolution_feedback=c.user_resolution_feedback, user_resolution_comment=c.user_resolution_comment,
        assigned_agent_name=agent_name, attachment_count=attachment_count, created_at=c.created_at,
        updated_at=c.updated_at, resolved_at=c.resolved_at,
    )
    if not staff:
        return ComplaintOut(**base).model_dump()
    return StaffComplaintOut(
        **base, user_id=c.user_id, assigned_agent_id=c.assigned_agent_id, assigned_at=c.assigned_at,
        requires_human_review=bool(c.requires_human_review), review_reason=c.review_reason,
        ai_provider=c.ai_provider, ai_model=c.ai_model, ai_latency_ms=c.ai_latency_ms,
        ai_fallback_used=bool(c.ai_fallback_used),
    ).model_dump()
