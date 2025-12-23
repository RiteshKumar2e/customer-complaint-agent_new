from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as complaint_router
from app.api.chat import router as chat_router
from app.routes.feedback import router as feedback_router

app = FastAPI(title="Quickfix Agentic AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://customer-complaint-agent-new.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaint_router)
app.include_router(chat_router)
app.include_router(feedback_router)

@app.get("/")
def root():
    return {"status": "Quickfix Backend Running"}
