"""Promote an existing user to super administrator by e-mail."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import User


def main():
    parser = argparse.ArgumentParser(description="Promote a Mecenato user to super administrator")
    parser.add_argument("--email", required=True, help="E-mail of the existing user")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=args.email.lower().strip()).first()
        if user is None:
            print("User not found.", file=sys.stderr)
            return 1
        user.role = "superadmin"
        user.active = True
        db.session.commit()
        print(f"Super admin provisioned: {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())