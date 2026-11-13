"""Public product-feedback form. Rate limited; all input is escaped before it reaches email HTML."""
import html
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.rate_limit import rate_limit
from app.core.validators import clean_text, normalize_email
from app.services.email_service import email_service

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    email: str
    rating: int = Field(ge=1, le=5)
    recommendation: int = Field(default=8, ge=0, le=10)
    message: str = Field(min_length=1, max_length=3000)
    # Honeypot: hidden in the UI, so only bots fill it in.
    website: Optional[str] = Field(default=None, max_length=200)

    @field_validator("email", mode="before")
    @classmethod
    def _email(cls, v):
        return normalize_email(v)

    @field_validator("name", "message", mode="before")
    @classmethod
    def _text(cls, v):
        return clean_text(v, 3000, "Field", required=True)


def _feedback_html(f: FeedbackRequest) -> str:
    nps = "Promoter" if f.recommendation >= 9 else "Passive" if f.recommendation >= 7 else "Detractor"
    color = "#10b981" if f.recommendation >= 9 else "#f59e0b" if f.recommendation >= 7 else "#ef4444"
    message = html.escape(f.message).replace("\n", "<br>")
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#f3f4f6;font-family:Segoe UI,Arial,sans-serif">
<table role="presentation" width="100%" style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:24px">
<tr><td><h2 style="margin:0 0 16px;color:#111827">New user feedback</h2>
<p style="margin:0 0 8px"><strong>Satisfaction:</strong> {f.rating}/5</p>
<p style="margin:0 0 8px"><strong>Recommendation:</strong> <span style="color:{color}">{f.recommendation}/10 ({nps})</span></p>
<p style="margin:16px 0 8px"><strong>Message</strong></p>
<div style="background:#f9fafb;border-radius:8px;padding:16px;color:#374151;line-height:1.6">{message}</div>
<p style="margin:16px 0 0;color:#6b7280;font-size:13px">From {html.escape(f.name)} &lt;{html.escape(f.email)}&gt;</p>
</td></tr></table></body></html>"""


@router.post("/feedback", dependencies=[Depends(rate_limit("feedback", 5, 600))])
def submit_feedback(feedback: FeedbackRequest):
    """Forward feedback to the configured ADMIN_NOTIFICATION_EMAIL."""
    if feedback.website:
        # Looks successful to the bot; nothing is sent.
        return {"status": "success", "delivered": False, "message": "Thank you for your feedback!"}
    queued = email_service.send_raw_to_admin(f"New feedback - {feedback.rating}/5", _feedback_html(feedback))
    return {"status": "success", "delivered": queued,
            "message": "Thank you for your feedback!"}
