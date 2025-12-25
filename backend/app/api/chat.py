from fastapi import APIRouter, HTTPException, Query
import traceback
from app.agents.chat_agent import handle_chat_message
from app.memory.redis_store import save_high_priority

router = APIRouter(prefix="/agent", tags=["Agent Chat"])

@router.post("/chat")
async def chat(message: str = Query(...)):
    """
    Async chat endpoint for high-concurrency AI assistance.
    """
    try:
        result = await handle_chat_message(message)

        if (result.get("type") == "complaint" and result.get("priority") == "High"):
            # Background tasks or separate threads would be even better for scaling, 
            # but keeping it simple and async for now as requested.
            save_high_priority(
                message,
                {
                    "category": result.get("category"),
                    "action": result.get("action"),
                }
            )

        return result

    except Exception as e:
        print("❌ CHAT ERROR:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
