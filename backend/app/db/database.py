"""
Database engine and session management — Turso (libSQL) only.

TURSO_DATABASE_URL must be a Turso URL (libsql://<db>.turso.io). The auth token
comes from TURSO_AUTH_TOKEN. There is deliberately no PostgreSQL, MySQL or
"fall back to a local SQLite file" path: if Turso is not configured the app
refuses to start rather than writing data somewhere it will be lost.

For automated tests and offline development an explicit `file:` URL is
accepted (e.g. TURSO_DATABASE_URL=file:local-dev.db). It uses the same libSQL
driver and the same code path, never a silent substitute; production rejects it.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import time

from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import ConfigError, get_settings
from app.core.logging import get_logger
from app.db import libsql_dialect  # noqa: F401  (registers sqlite+turso)

logger = get_logger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_time() -> datetime:
    """Current time in IST as a naive datetime (the existing data uses this convention)."""
    return datetime.now(IST).replace(tzinfo=None)


now = get_ist_time


def resolve_turso_target(url: str, token: str) -> Tuple[str, str]:
    """
    Split TURSO_DATABASE_URL into (database, auth_token) for libsql.connect().

    Older deployments embedded the token as `?authToken=...`; that still works,
    but TURSO_AUTH_TOKEN takes precedence and is the documented way.
    """
    if not url:
        raise ConfigError(
            "TURSO_DATABASE_URL is not set. This application stores all data in Turso; "
            "create a database with `turso db create` and set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN."
        )
    scheme = url.split(":", 1)[0].lower()
    if scheme in ("postgres", "postgresql", "mysql", "mariadb", "sqlite"):
        raise ConfigError(f"TURSO_DATABASE_URL uses unsupported scheme '{scheme}'. Only Turso (libsql://) is supported.")

    if scheme == "file":
        return url[len("file:"):], ""

    if scheme not in ("libsql", "https", "http", "wss", "ws"):
        raise ConfigError("TURSO_DATABASE_URL must look like libsql://<database>-<org>.turso.io")

    parts = urlsplit(url)
    params = dict(parse_qsl(parts.query))
    url_token = params.pop("authToken", "") or params.pop("auth_token", "")
    database = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), ""))
    auth_token = token or url_token
    if url_token and not token:
        logger.warning("Turso auth token found in TURSO_DATABASE_URL; move it to TURSO_AUTH_TOKEN.")
    return database, auth_token


def describe_target(database: str) -> str:
    if "://" in database:
        return urlsplit(database).netloc
    return f"local libSQL file ({database})"


def build_engine():
    settings = get_settings()
    database, auth_token = resolve_turso_target(settings.turso_database_url, settings.turso_auth_token)
    if settings.is_production and "://" not in database:
        raise ConfigError("Production requires a remote Turso database, not a local libSQL file.")

    def creator():
        return libsql_dialect.connect(database, auth_token=auth_token, timeout=settings.db_connect_timeout)

    engine = create_engine(
        "sqlite+turso://",
        creator=creator,
        pool_size=5,
        max_overflow=10,
        pool_timeout=15,
        # Hrana streams expire server-side when idle; recycle before that and
        # ping on checkout so a stale connection is replaced, not surfaced.
        pool_recycle=240,
        # A ping on *every* checkout costs a full round trip to Turso per request
        # (~0.2-0.5 s when the app and database are on different continents).
        # Only connections idle longer than IDLE_PING_SECONDS are pinged instead.
        pool_pre_ping=False,
    )
    _install_idle_ping(engine)
    logger.info("Database engine ready: Turso/libSQL @ %s", describe_target(database))
    return engine


IDLE_PING_SECONDS = 20


def _install_idle_ping(target_engine) -> None:
    @event.listens_for(target_engine, "checkin")
    def _remember_use(dbapi_connection, record):
        record.info["last_used"] = time.monotonic()

    @event.listens_for(target_engine, "checkout")
    def _ping_if_idle(dbapi_connection, record, proxy):
        last = record.info.get("last_used")
        if last is None or time.monotonic() - last < IDLE_PING_SECONDS:
            return  # brand-new or recently used: no extra round trip
        try:
            dbapi_connection.execute("SELECT 1").fetchone()
        except Exception as error:  # includes driver panics, translated by the dialect
            # The pool discards this connection and transparently opens a new one.
            raise exc.DisconnectionError() from error


engine = build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

Base = declarative_base()


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, rolled back on error."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope for background jobs and scripts."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database() -> dict:
    """Lightweight connectivity check used by /health/ready."""
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).scalar()
    return {"database": "ok"}
