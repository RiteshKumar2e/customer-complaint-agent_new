from fastapi import FastAPI, Request
import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.db.database import engine
from app.db import models
from app.api.routes import router as complaint_router
from app.api.chat import router as chat_router
from app.routes.feedback import router as feedback_router
from app.routes.auth import router as auth_router
from app.routes.agent_module import router as agent_router

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Run custom migrations (add missing columns)
from app.db.database import run_migrations
run_migrations()

app = FastAPI(title="Quickfix Agentic AI")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # NOTE: Do not call `await request.body()` here — the body stream is already
    # consumed during request parsing, so re-reading it raises ClientDisconnect
    # and crashes the handler (client sees a reset instead of a 422).
    # FastAPI attaches the raw body to the exception as `exc.body`.
    print(f"❌ VALIDATION ERROR: {exc.errors()}")
    print(f"📋 REQUEST BODY: {exc.body}")
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"

# Origins that are always allowed. FRONTEND_URL may hold several comma-separated
# URLs so a single env var can cover apex + www + a staging domain.
ALLOWED_ORIGINS = [
    "https://riteshkr.online",
    "http://riteshkr.online",
    "https://www.riteshkr.online",
    "http://www.riteshkr.online",
]

if not IS_PRODUCTION:
    ALLOWED_ORIGINS += [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

ALLOWED_ORIGINS += [
    origin.strip().rstrip("/")
    for origin in os.getenv("FRONTEND_URL", "").split(",")
    if origin.strip()
]

# Deduplicate while keeping order. Never let "*" in here: it is meaningless
# alongside allow_credentials=True and would make Starlette echo back any
# origin that asks.
ALLOWED_ORIGINS = list(dict.fromkeys(o for o in ALLOWED_ORIGINS if o != "*"))

# Starlette matches allow_origins by exact string, so "https://*.vercel.app"
# never matched anything. Preview deployments need a regex instead.
ALLOWED_ORIGIN_REGEX = r"https://[a-z0-9-]+\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
    max_age=86400,
)


@app.middleware("http")
async def cross_origin_isolation_headers(request: Request, call_next):
    # The Google Sign-In popup talks back to its opener via window.opener /
    # window.closed. A COOP of "same-origin" severs that handle and the sign-in
    # silently never resolves, so this API must stay on the permissive variant
    # that still isolates us from unrelated top-level windows.
    response = await call_next(request)
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin-allow-popups")
    # Responses are consumed by the frontend on a different origin, so the
    # default "same-origin" CORP would block them.
    response.headers.setdefault("Cross-Origin-Resource-Policy", "cross-origin")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response

app.include_router(complaint_router)
app.include_router(chat_router)
app.include_router(feedback_router)
app.include_router(auth_router)
app.include_router(agent_router)

@app.get("/")
def root():
    return {"status": "Quickfix Backend Running"}


@app.get("/health")
def health():
    # Deliberately does no DB or LLM work: this is the endpoint load tests and
    # platform health checks hit, so it must measure the web tier alone.
    return {"status": "ok"}
