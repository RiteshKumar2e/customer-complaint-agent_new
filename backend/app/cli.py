"""
Server-side administration (the only way to create the first admin).

    python -m app.cli promote --email someone@example.com --role admin
    python -m app.cli promote --email agent@example.com --role agent --department Billing
    python -m app.cli list-staff

Run it where TURSO_DATABASE_URL / TURSO_AUTH_TOKEN point at the target database
(e.g. a Render shell). The account must already exist and have a verified email.
"""
import argparse
import sys

from app.core.logging import configure_logging


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    promote = sub.add_parser("promote", help="set a user's role")
    promote.add_argument("--email", required=True)
    promote.add_argument("--role", required=True, choices=["customer", "agent", "admin"])
    promote.add_argument("--department", choices=["Billing", "Technical", "Delivery", "Service", "Security", "Other"])
    sub.add_parser("list-staff", help="list agents and admins")
    args = parser.parse_args(argv)

    configure_logging(json_output=False)
    from sqlalchemy import select

    from app.core.validators import normalize_email
    from app.db.database import SessionLocal
    from app.db.models import User
    from app.services.auth_service import revoke_all_sessions

    db = SessionLocal()
    try:
        if args.command == "list-staff":
            for u in db.execute(select(User).where(User.role.in_(("agent", "admin"))).order_by(User.role)).scalars():
                print(f"{u.role:6} {u.email:40} {u.department or '-':10} active={u.is_active}")
            return 0
        email = normalize_email(args.email)
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None:
            print(f"No account for {email}. The person must sign up and verify their email first.")
            return 1
        if not user.email_verified:
            print(f"{email} has not verified their email yet; refusing to grant a role.")
            return 1
        user.role = args.role
        if args.department:
            user.department = args.department
        revoke_all_sessions(db, user)
        db.commit()
        print(f"{email} is now {args.role}. Existing sessions were signed out.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
