"""
Create the schema in Turso over the HTTP API.

The app itself calls `Base.metadata.create_all()` on startup, which is enough on
Render. This script exists for Windows: the sqlalchemy-libsql dialect has no
Windows wheel, so `create_all()` cannot run locally against Turso. It talks to
Turso over plain HTTP instead, generating the DDL from the same ORM models so
the two can't drift.

Usage:  python init_turso.py [--drop]
"""

import os
import sys
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import sqlite

load_dotenv()

try:
    import libsql_client
except ImportError:
    sys.exit("Missing dependency. Run: pip install libsql-client")

from app.db.models import Base


def _client():
    raw = os.getenv("TURSO_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not raw:
        sys.exit("No TURSO_DATABASE_URL / DATABASE_URL found in .env")

    parsed = urlparse(raw)
    token = parse_qs(parsed.query).get("authToken", [None])[0]
    if not token:
        sys.exit("No authToken in the Turso URL")

    print(f"Connecting to https://{parsed.netloc}")
    return libsql_client.create_client_sync(
        url=f"https://{parsed.netloc}", auth_token=token
    )


def main():
    drop = "--drop" in sys.argv
    tables = Base.metadata.sorted_tables

    with _client() as client:
        if drop:
            # Children first, so foreign keys never dangle.
            for table in reversed(tables):
                client.execute(f"DROP TABLE IF EXISTS {table.name}")
                print(f"  dropped {table.name}")

        for table in tables:
            ddl = str(
                CreateTable(table, if_not_exists=True).compile(dialect=sqlite.dialect())
            ).strip()
            client.execute(ddl)
            print(f"  created {table.name}")

        existing = [
            r[0]
            for r in client.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).rows
        ]
        print(f"\nTables now in Turso ({len(existing)}): {existing}")


if __name__ == "__main__":
    main()
