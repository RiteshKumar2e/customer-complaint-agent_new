"""
Copy a Turso database (schema + all rows) into a local libSQL/SQLite file.

READ-ONLY on the source. Uses:
  * backup before a production deploy / migration
  * rehearsing migrations on a copy of real data:
        python scripts/turso_snapshot.py --out snapshot.db
        TURSO_DATABASE_URL=file:snapshot.db python -m app.db.migrate
  * seeding a separate staging database from a copy of production:
        turso db create quickfix-staging --from-file snapshot.db

Source defaults to TURSO_DATABASE_URL / TURSO_AUTH_TOKEN; override with
--source-url / --source-token. The output file contains personal data —
keep it out of git (it is .gitignored as *.db) and delete it when done.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import libsql  # noqa: E402
from dotenv import load_dotenv  # noqa: E402


def main(argv=None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, help="local .db file to create (must not exist)")
    parser.add_argument("--source-url", default=os.getenv("TURSO_DATABASE_URL", ""))
    parser.add_argument("--source-token", default=os.getenv("TURSO_AUTH_TOKEN", ""))
    args = parser.parse_args(argv)

    from app.db.database import resolve_turso_target

    if os.path.exists(args.out):
        print(f"{args.out} already exists; refusing to overwrite.")
        return 1
    database, token = resolve_turso_target(args.source_url, args.source_token)
    src = libsql.connect(database, auth_token=token) if token else libsql.connect(database)
    dst = libsql.connect(args.out, isolation_level=None)

    objects = src.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
        "AND name NOT LIKE '_litestream%' AND name NOT LIKE 'libsql_%' ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END"
    ).fetchall()
    dst.execute("PRAGMA foreign_keys = OFF")
    dst.execute("BEGIN")
    total = 0
    for kind, name, sql in objects:
        if kind == "table" and name.startswith("_qf_"):
            continue  # scratch tables from live tests
        dst.execute(sql)
        if kind != "table":
            continue
        rows = src.execute(f'SELECT * FROM "{name}"').fetchall()
        if rows:
            marks = ",".join("?" * len(rows[0]))
            dst.executemany(f'INSERT INTO "{name}" VALUES ({marks})', [tuple(r) for r in rows])
        total += len(rows)
        print(f"  {name}: {len(rows)} rows")
    dst.execute("COMMIT")
    print(f"Snapshot written to {args.out} ({total} rows).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
