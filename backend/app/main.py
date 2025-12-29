from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.db.database import engine
from app.db import models
from app.api.routes import router as complaint_router
from app.api.chat import router as chat_router
from app.routes.feedback import router as feedback_router
from app.routes.auth import router as auth_router

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Run custom migrations (add missing columns)
from app.db.database import run_migrations
run_migrations()

app = FastAPI(title="Quickfix Agentic AI")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"❌ VALIDATION ERROR: {exc.errors()}")
    print(f"📋 REQUEST BODY: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(await request.body())},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://customer-complaint-agent-new-vpfu.vercel.app",
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
app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "Quickfix Backend Running"}
