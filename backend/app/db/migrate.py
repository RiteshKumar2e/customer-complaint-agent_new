"""
Apply pending schema migrations to the configured Turso database.

    python -m app.db.migrate            # apply pending migrations
    python -m app.db.migrate --status   # list applied / pending, change nothing
"""
import argparse
import sys

from app.core.logging import configure_logging


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--status", action="store_true", help="show migration status without applying anything")
    args = parser.parse_args(argv)

    configure_logging(json_output=False)
    from app.db.database import engine
    from app.db.migrations import applied_versions, pending_migrations, run_migrations

    if args.status:
        print("applied:", ", ".join(applied_versions(engine)) or "(none)")
        print("pending:", ", ".join(f"{m.version}_{m.name}" for m in pending_migrations(engine)) or "(none)")
        return 0

    applied = run_migrations(engine)
    print("applied now:", ", ".join(applied) or "(nothing pending)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
