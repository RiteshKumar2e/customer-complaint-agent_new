"""
Checks against a REAL Turso database. Skipped unless TURSO_TEST_DATABASE_URL is set.

    TURSO_TEST_DATABASE_URL=libsql://... TURSO_TEST_AUTH_TOKEN=... pytest tests/test_turso_live.py

Only a uniquely named scratch table is created, used and dropped; existing
tables and data are never read or modified. Point it at a staging database.
"""
import os
import secrets

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.db import libsql_dialect

URL = os.getenv("TURSO_TEST_DATABASE_URL", "")
TOKEN = os.getenv("TURSO_TEST_AUTH_TOKEN", "")
pytestmark = pytest.mark.skipif(not URL, reason="TURSO_TEST_DATABASE_URL not set")


@pytest.fixture(scope="module")
def remote():
    from app.db.database import resolve_turso_target

    database, token = resolve_turso_target(URL, TOKEN)
    eng = create_engine("sqlite+turso://", creator=lambda: libsql_dialect.connect(database, auth_token=token),
                        pool_pre_ping=True)
    table = f"_qf_live_{secrets.token_hex(4)}"
    with eng.begin() as conn:
        conn.execute(text(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE, n INTEGER)"))
    yield eng, table
    with eng.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
    eng.dispose()


def test_connect_and_crud(remote):
    eng, table = remote
    with eng.begin() as conn:
        conn.execute(text(f"INSERT INTO {table} (email, n) VALUES ('a@x.com', 1)"))
        conn.execute(text(f"UPDATE {table} SET n = 2 WHERE email = 'a@x.com'"))
    with eng.connect() as conn:
        assert conn.execute(text(f"SELECT n FROM {table} WHERE email='a@x.com'")).scalar() == 2
    with eng.begin() as conn:
        conn.execute(text(f"DELETE FROM {table} WHERE email='a@x.com'"))


def test_transaction_rollback(remote):
    eng, table = remote
    with pytest.raises(IntegrityError):
        with eng.begin() as conn:
            conn.execute(text(f"INSERT INTO {table} (email) VALUES ('t@x.com')"))
            conn.execute(text(f"INSERT INTO {table} (email) VALUES ('t@x.com')"))
    with eng.connect() as conn:
        assert conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE email='t@x.com'")).scalar() == 0


def test_bad_token_is_an_operational_error():
    from sqlalchemy.exc import OperationalError

    from app.db.database import resolve_turso_target

    database, _ = resolve_turso_target(URL, TOKEN)
    eng = create_engine("sqlite+turso://", creator=lambda: libsql_dialect.connect(database, auth_token="bad-token"))
    with pytest.raises(OperationalError):
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
