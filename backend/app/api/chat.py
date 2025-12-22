from fastapi import APIRouter, HTTPException
import traceback

from app.agents.chat_agent import handle_chat_message
from app.memory.redis_store import save_high_priority

router = APIRouter(prefix="/agent", tags=["Agent Chat"])


@router.post("/chat")
def chat(message: str):
    try:
        result = handle_chat_message(message)

        if (
            result.get("type") == "complaint"
            and result.get("priority") == "High"
        ):
            save_high_priority(
                message,
                {
                    "category": result.get("category"),
                    "action": result.get("action"),
                }
            )

        return result

    except Exception as e:
        print("❌ CHAT ERROR TRACEBACK:")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
