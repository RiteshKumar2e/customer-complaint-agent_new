"""QuickFix AI API entry point."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings, validate_for_startup
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware

settings = get_settings()
configure_logging(json_output=not settings.is_test)
logger = get_logger("app.main")
for warning in validate_for_startup(settings):  # raises ConfigError in production
    logger.warning(warning)

from app.db.database import check_database, engine  # noqa: E402  (after config validation)
from app.db.migrations import pending_migrations, run_migrations  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.run_migrations_on_startup:
        applied = await asyncio.to_thread(run_migrations, engine)
        if applied:
            logger.info("Applied migrations: %s", ", ".join(applied))
    else:
        pending = await asyncio.to_thread(pending_migrations, engine)
        if pending:
            raise RuntimeError("Database schema is out of date; run `python -m app.db.migrate` "
                               f"(pending: {', '.join(m.version for m in pending)})")
    if not settings.is_test:
        from app.services.auto_resolver import auto_resolver

        asyncio.create_task(auto_resolver.resume_pending())
    yield


app = FastAPI(
    title="QuickFix AI API",
    description="Complaint management with AI triage. Authenticate with `POST /auth/login` and send "
                "`Authorization: Bearer <access_token>`.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

register_exception_handlers(app)

origins = list(settings.frontend_urls)
if not settings.is_production:
    origins += ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(o for o in origins if o and o != "*")),
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,  # bearer tokens, no cookies
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Content-Disposition", "X-Request-ID", "Retry-After"],
    max_age=86400,
)
app.add_middleware(RequestContextMiddleware, max_body_bytes=settings.max_request_bytes,
                   upload_paths_max_bytes=settings.max_upload_bytes)

from app.api.chat import router as chat_router  # noqa: E402
from app.api.routes import router as complaint_router  # noqa: E402
from app.routes.admin import router as admin_router  # noqa: E402
from app.routes.agent_module import router as agent_router  # noqa: E402
from app.routes.auth import router as auth_router  # noqa: E402
from app.routes.feedback import router as feedback_router  # noqa: E402
from app.routes.notifications import router as notifications_router  # noqa: E402

for router in (auth_router, complaint_router, agent_router, admin_router, notifications_router,
               feedback_router, chat_router):
    app.include_router(router)


# Uptime monitors commonly probe with HEAD; GET-only routes answered 405.
@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def root():
    return {"service": "quickfix-api", "status": "ok"}


@app.api_route("/health", methods=["GET", "HEAD"], tags=["health"])
def health():
    """Liveness: the process is up. Does no database or AI work."""
    return {"status": "ok"}


@app.api_route("/health/ready", methods=["GET", "HEAD"], tags=["health"])
def ready():
    """Readiness: Turso is reachable."""
    try:
        check_database()
    except Exception:
        logger.exception("Readiness check failed")
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "unreachable"})
    return {"status": "ok", "database": "ok"}
