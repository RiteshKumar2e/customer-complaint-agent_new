"""
Audit and repair the Turso schema over the HTTP API.

The app calls `Base.metadata.create_all()` on startup, which covers Render. This
script exists for Windows, where the sqlalchemy-libsql dialect has no wheel and
`create_all()` therefore cannot run against Turso. It talks to Turso over plain
HTTP instead, deriving everything from the ORM models so the two can't drift.

By default it only reports. Pass --fix to apply the missing pieces.

Usage:
    python init_turso.py            # audit only
    python init_turso.py --fix      # create missing tables/columns/indexes
"""

import os
import sys
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import sqlite

load_dotenv()

try:
    import libsql_client
except ImportError:
    sys.exit("Missing dependency. Run: pip install libsql-client")

from app.db.models import Base

DIALECT = sqlite.dialect()


def _client():
    raw = os.getenv("TURSO_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not raw:
        sys.exit("No TURSO_DATABASE_URL / DATABASE_URL found in .env")

    parsed = urlparse(raw)
    token = parse_qs(parsed.query).get("authToken", [None])[0]
    if not token:
        sys.exit("No authToken in the Turso URL")

    print(f"Connecting to https://{parsed.netloc}\n")
    return libsql_client.create_client_sync(
        url=f"https://{parsed.netloc}", auth_token=token
    )


def _live_tables(client):
    return {
        r[0]
        for r in client.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).rows
    }


def _live_columns(client, table):
    return {r[1] for r in client.execute(f"PRAGMA table_info({table})").rows}


def _live_indexes(client, table):
    return {r[1] for r in client.execute(f"PRAGMA index_list({table})").rows}


def main():
    fix = "--fix" in sys.argv
    problems = 0
    repaired = 0

    with _client() as client:
        live_tables = _live_tables(client)

        for table in Base.metadata.sorted_tables:
            print(f"[{table.name}]")

            if table.name not in live_tables:
                problems += 1
                print("  MISSING TABLE")
                if fix:
                    client.execute(
                        str(CreateTable(table, if_not_exists=True).compile(dialect=DIALECT)).strip()
                    )
                    repaired += 1
                    print("  -> created")
                else:
                    continue

            # --- columns ---
            live_cols = _live_columns(client, table.name)
            for col in table.columns:
                if col.name in live_cols:
                    continue
                problems += 1
                print(f"  MISSING COLUMN: {col.name}")
                if not fix:
                    continue
                col_type = col.type.compile(dialect=DIALECT)
                # SQLite cannot add a NOT NULL column without a default, so the
                # column is added nullable; the model still enforces it on write.
                try:
                    client.execute(
                        f"ALTER TABLE {table.name} ADD COLUMN {col.name} {col_type}"
                    )
                    repaired += 1
                    print(f"  -> added ({col_type})")
                except Exception as e:
                    print(f"  -> FAILED: {e}")

            # --- indexes (CreateTable does not emit these) ---
            live_idx = _live_indexes(client, table.name)
            for idx in table.indexes:
                # Auto-indexes backing UNIQUE constraints are named sqlite_autoindex_*
                # and already exist; only explicit index=True ones need creating.
                if idx.name in live_idx:
                    continue
                problems += 1
                print(f"  MISSING INDEX: {idx.name}")
                if not fix:
                    continue
                try:
                    ddl = str(CreateIndex(idx, if_not_exists=True).compile(dialect=DIALECT)).strip()
                    client.execute(ddl)
                    repaired += 1
                    print("  -> created")
                except Exception as e:
                    print(f"  -> FAILED: {e}")

            cols = len(table.columns)
            print(f"  ok: {cols} columns, {len(table.indexes)} declared indexes\n")

        print("=" * 55)
        if problems == 0:
            print("Schema matches the models. Nothing to do.")
        elif fix:
            print(f"Found {problems} issue(s), repaired {repaired}.")
        else:
            print(f"Found {problems} issue(s). Re-run with --fix to apply.")


if __name__ == "__main__":
    main()
