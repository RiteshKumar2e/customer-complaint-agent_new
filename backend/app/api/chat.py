"""Public support chatbot (rate limited; no account data is exposed through it)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.agents.chat_agent import handle_chat_message
from app.core.rate_limit import rate_limit

router = APIRouter(prefix="/agent", tags=["chatbot"])


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=2000)


@router.post("/chat", dependencies=[Depends(rate_limit("chat", 20, 60))])
async def chat(request: ChatRequest):
    """Answer a question or give an instant (unsaved) complaint analysis."""
    result = await handle_chat_message(request.message)
    # Provenance fields are internal; the public chatbot only needs the answer.
    for internal in ("ai_error", "injection_flags", "ai_attempts"):
        result.pop(internal, None)
    return result
