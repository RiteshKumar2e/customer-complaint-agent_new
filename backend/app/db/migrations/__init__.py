"""
Versioned, forward-only schema migrations for Turso.

Each migration runs in its own transaction (libSQL supports transactional DDL;
verified against Turso). The first statement of every migration claims its row
in `schema_migrations`, which also takes the database write lock, so two app
instances starting at once cannot both apply the same migration.

Run manually with:  python -m app.db.migrate
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    upgrade: Callable[[Connection], None]


def _load() -> List[Migration]:
    from app.db.migrations import m0001_legacy_baseline, m0002_auth_rbac_workflow

    return [
        Migration("0001", "legacy_baseline", m0001_legacy_baseline.upgrade),
        Migration("0002", "auth_rbac_workflow", m0002_auth_rbac_workflow.upgrade),
    ]


MIGRATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) NOT NULL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    applied_at DATETIME NOT NULL
)
"""


def applied_versions(engine: Engine) -> List[str]:
    with engine.begin() as conn:
        conn.execute(text(MIGRATIONS_TABLE_DDL))
        return [row[0] for row in conn.execute(text("SELECT version FROM schema_migrations ORDER BY version"))]


def pending_migrations(engine: Engine) -> List[Migration]:
    done = set(applied_versions(engine))
    return [m for m in _load() if m.version not in done]


def run_migrations(engine: Engine) -> List[str]:
    """Apply every pending migration; return the versions applied now."""
    from app.db.database import get_ist_time
    from app.db.libsql_dialect import IntegrityError as DriverIntegrityError
    from sqlalchemy.exc import IntegrityError

    applied_now: List[str] = []
    for migration in pending_migrations(engine):
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO schema_migrations (version, name, applied_at) VALUES (:v, :n, :t)"),
                    {"v": migration.version, "n": migration.name, "t": get_ist_time()},
                )
                logger.info("Applying migration %s_%s", migration.version, migration.name)
                migration.upgrade(conn)
        except IntegrityError as exc:
            if isinstance(exc.orig, DriverIntegrityError) and "schema_migrations" in str(exc.orig):
                logger.info("Migration %s already applied by another instance", migration.version)
                continue
            raise
        applied_now.append(migration.version)
        logger.info("Migration %s applied", migration.version)
    return applied_now


# ---------------------------------------------------------------------------
# Helpers for migration modules
# ---------------------------------------------------------------------------

def table_exists(conn: Connection, table: str) -> bool:
    return conn.execute(
        text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:t"), {"t": table}
    ).first() is not None


def column_names(conn: Connection, table: str) -> List[str]:
    return [row[1] for row in conn.execute(text(f'PRAGMA table_info("{table}")'))]


def index_exists(conn: Connection, name: str) -> bool:
    return conn.execute(
        text("SELECT 1 FROM sqlite_master WHERE type='index' AND name=:n"), {"n": name}
    ).first() is not None


def add_column(conn: Connection, table: str, column: str, ddl: str) -> None:
    if column not in column_names(conn, table):
        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {column} {ddl}'))
