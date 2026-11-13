"""
SQLAlchemy dialect for Turso built on the official `libsql` Python SDK.

Why not `sqlalchemy-libsql`? It depends on `libsql-experimental`, which has no
Windows wheels and is superseded by the official `libsql` package. This module
is the small amount of glue needed to run SQLAlchemy's SQLite dialect on top of
`libsql` against a remote Turso database (or a local libSQL file in tests):

* `libsql` reports every failure as a bare `ValueError`. SQLAlchemy only wraps
  exceptions that derive from the DB-API `Error` class, so the shim below
  re-raises them as proper `IntegrityError` / `OperationalError` / ... classes.
* Connections run with `isolation_level=None` and the shim opens the
  transaction itself with `BEGIN IMMEDIATE` right before the first write,
  DDL or SAVEPOINT (like Python's sqlite3 module, but also covering DDL so
  migrations are atomic). Plain reads run in autocommit, so an idle session
  never holds a read snapshot that a later write would have to upgrade —
  the classic SQLite "database is locked" failure under concurrency.
* Foreign-key enforcement is switched on for every connection.
"""
from __future__ import annotations

import datetime
import decimal
import re
import types
from typing import Any, Optional, Sequence

import libsql
from sqlalchemy import pool
from sqlalchemy.dialects import registry
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite

# ---------------------------------------------------------------------------
# DB-API 2.0 exception hierarchy on top of libsql
# ---------------------------------------------------------------------------
Error = libsql.Error


class Warning(Exception):  # noqa: A001 - DB-API name
    pass


class InterfaceError(Error):
    pass


class DatabaseError(Error):
    pass


class DataError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class IntegrityError(DatabaseError):
    pass


class InternalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    pass


_INTEGRITY = re.compile(r"constraint failed|UNIQUE constraint|FOREIGN KEY constraint|NOT NULL constraint|CHECK constraint", re.I)
_CONNECTION = re.compile(
    r"api error|stream error|stream expired|baton|connection (refused|reset|closed)|timed? ?out|"
    r"error sending request|dns error|Host not found|tcp connect|broken pipe|HTTP status",
    re.I,
)
_PROGRAMMING = re.compile(r"syntax error|could not be parsed|no such (table|column)|has no column", re.I)


def translate_error(exc: BaseException) -> BaseException:
    """Map a raw libsql failure onto the DB-API hierarchy."""
    if isinstance(exc, Error):
        return exc
    message = str(exc)
    # Hrana wraps the real SQLite message; keep it readable but drop transport noise.
    match = re.search(r'message: "(?:SQLite error: )?([^"]+)"', message)
    clean = match.group(1) if match else message
    if _INTEGRITY.search(message):
        return IntegrityError(clean)
    if _PROGRAMMING.search(message):
        return OperationalError(clean)
    if _CONNECTION.search(message):
        return OperationalError(f"database unavailable: {clean[:200]}")
    return DatabaseError(clean)


def _adapt(value: Any) -> Any:
    """sqlite3's default adapters, which libsql lacks (it rejects datetime etc.)."""
    if isinstance(value, bool):
        return int(value)
    if value is None or isinstance(value, (str, int, float, bytes)):
        return value
    if isinstance(value, datetime.datetime):
        return value.isoformat(" ")
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (bytearray, memoryview)):
        return bytes(value)
    return value


def _params(parameters) -> tuple:
    if not parameters:
        return ()
    return tuple(_adapt(v) for v in parameters)


def _call(fn, *args):
    try:
        return fn(*args)
    except (ValueError, RuntimeError) as exc:
        raise translate_error(exc) from exc


_TX_TRIGGER = re.compile(r"^\s*(INSERT|UPDATE|DELETE|REPLACE|CREATE|DROP|ALTER|SAVEPOINT)\b", re.I)


class Cursor:
    def __init__(self, raw, conn: "Connection"):
        self._raw = raw
        self._conn = conn

    def _ensure_transaction(self, sql: str) -> None:
        if not self._conn.in_tx and _TX_TRIGGER.match(sql):
            # Separate cursor: libsql accumulates rowcount per cursor, so a BEGIN on
            # this one would inflate the following UPDATE's rowcount (StaleDataError).
            _call(self._conn._raw.execute, "BEGIN IMMEDIATE")
            self._conn.in_tx = True

    @property
    def description(self):
        return self._raw.description

    @property
    def rowcount(self):
        return self._raw.rowcount

    @property
    def lastrowid(self):
        return self._raw.lastrowid

    @property
    def arraysize(self):
        return self._raw.arraysize

    @arraysize.setter
    def arraysize(self, value):
        self._raw.arraysize = value

    def execute(self, sql: str, parameters: Sequence[Any] = ()):
        self._ensure_transaction(sql)
        _call(self._raw.execute, sql, _params(parameters))
        return self

    def executemany(self, sql: str, seq_of_parameters):
        self._ensure_transaction(sql)
        _call(self._raw.executemany, sql, [_params(p) for p in seq_of_parameters])
        return self

    def fetchone(self):
        return _call(self._raw.fetchone)

    def fetchmany(self, size: Optional[int] = None):
        return _call(self._raw.fetchmany, size if size is not None else self._raw.arraysize)

    def fetchall(self):
        return _call(self._raw.fetchall)

    def close(self):
        try:
            self._raw.close()
        except Exception:
            pass

    def __iter__(self):
        while True:
            row = self.fetchone()
            if row is None:
                return
            yield row


class Connection:
    """
    DB-API connection wrapper with explicit transaction control.

    Transaction state is tracked here rather than read from the driver: a fresh
    remote libsql connection reports in_transaction=True until its first
    statement, which would otherwise make every write autocommit.
    """

    def __init__(self, raw):
        self._raw = raw
        self.in_tx = False

    def cursor(self):
        return Cursor(_call(self._raw.cursor), self)

    def execute(self, sql: str, parameters: Sequence[Any] = ()):
        return self.cursor().execute(sql, parameters)

    @property
    def in_transaction(self) -> bool:
        return self.in_tx

    def commit(self):
        if self.in_tx:
            _call(self._raw.execute, "COMMIT")
            self.in_tx = False

    def rollback(self):
        if not self.in_tx:
            return
        try:
            _call(self._raw.execute, "ROLLBACK")
        except DatabaseError as exc:
            if "no transaction is active" not in str(exc).lower():
                raise
        finally:
            self.in_tx = False

    def close(self):
        try:
            self.rollback()
        except Exception:
            pass
        try:
            self._raw.close()
        except Exception:
            pass

    # SQLAlchemy's SQLite dialect probes this; libsql has no user functions.
    def create_function(self, *args, **kwargs):  # pragma: no cover - never called
        raise NotSupportedError("libsql does not support user-defined functions")


def connect(database: str, auth_token: str = "", timeout: float = 10.0, **_ignored) -> Connection:
    kwargs = {"isolation_level": None, "timeout": timeout}
    if auth_token:
        kwargs["auth_token"] = auth_token
    try:
        raw = libsql.connect(database, **kwargs)
    except (ValueError, RuntimeError) as exc:
        raise translate_error(exc) from exc
    conn = Connection(raw)
    conn.execute("PRAGMA foreign_keys = ON")
    if "://" not in database:
        # Local libSQL files (tests / offline dev): readers must not block the writer.
        conn.execute("PRAGMA journal_mode = WAL").fetchall()
        conn.execute("PRAGMA busy_timeout = 5000")
    return conn


# A module-like object that SQLAlchemy treats as the DB-API module.
dbapi = types.SimpleNamespace(
    connect=connect,
    paramstyle="qmark",
    apilevel="2.0",
    threadsafety=1,
    sqlite_version_info=libsql.sqlite_version_info,
    sqlite_version=".".join(str(p) for p in libsql.sqlite_version_info),
    version_info=(0, 1, 11),
    Error=Error,
    Warning=Warning,
    InterfaceError=InterfaceError,
    DatabaseError=DatabaseError,
    DataError=DataError,
    OperationalError=OperationalError,
    IntegrityError=IntegrityError,
    InternalError=InternalError,
    ProgrammingError=ProgrammingError,
    NotSupportedError=NotSupportedError,
    Binary=bytes,
)


class TursoDialect(SQLiteDialect_pysqlite):
    """`sqlite+turso://` — SQLite SQL dialect, libsql transport."""

    driver = "turso"
    supports_statement_cache = True
    # Native SAVEPOINT support verified against Turso.
    supports_savepoints = True

    @classmethod
    def import_dbapi(cls):
        return dbapi

    @classmethod
    def get_pool_class(cls, url):
        # The parent picks SingletonThreadPool for URLs without a file path,
        # which would pin a single remote connection to one thread.
        return pool.QueuePool

    def on_connect(self):
        # The pysqlite hook registers a REGEXP function; libsql cannot.
        return None

    def do_begin(self, dbapi_connection):
        # Deferred: the cursor shim issues BEGIN IMMEDIATE before the first write.
        return None

    def set_isolation_level(self, dbapi_connection, level):
        # Transactions are always explicit; isolation is SERIALIZABLE in SQLite.
        return None

    def get_isolation_level(self, dbapi_connection):
        return "SERIALIZABLE"

    def is_disconnect(self, e, connection, cursor):
        if isinstance(e, OperationalError) and "database unavailable" in str(e):
            return True
        return False

    def do_ping(self, dbapi_connection):
        dbapi_connection.execute("SELECT 1").fetchone()
        return True


registry.register("sqlite.turso", __name__, "TursoDialect")
