"""Create the schema and optionally provision the first admin user."""

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import Club, User


def main():
    parser = argparse.ArgumentParser(description="Initialize the Mecenato database")
    parser.add_argument("--admin-name", default=os.getenv("ADMIN_NAME", "Administrador"))
    parser.add_argument("--admin-email", default=os.getenv("ADMIN_EMAIL"))
    parser.add_argument("--admin-password", default=os.getenv("ADMIN_PASSWORD"))
    parser.add_argument("--club-name", default=os.getenv("CLUB_NAME", "Clube Mecenato"))
    parser.add_argument("--club-description", default=os.getenv("CLUB_DESCRIPTION", "Clube de leitura Mecenato."))
    parser.add_argument("--club-color", default=os.getenv("CLUB_COLOR", "#e56b4f"))
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        db.create_all()
        club = Club.query.order_by(Club.id).first()
        if club is None:
            club = Club(
                name=args.club_name.strip(),
                description=args.club_description.strip(),
                color_tag=args.club_color.strip(),
            )
            db.session.add(club)
            db.session.commit()
            print(f"Club provisioned: {club.name}")
        if args.admin_email and args.admin_password:
            email = args.admin_email.lower().strip()
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User(name=args.admin_name.strip(), email=email, role="admin")
                db.session.add(user)
            else:
                user.name = args.admin_name.strip()
                user.role = "admin"
            user.set_password(args.admin_password)
            db.session.commit()
            print(f"Admin provisioned: {user.email}")
            if club not in user.clubs:
                user.clubs.append(club)
                db.session.commit()
                print(f"Admin joined: {club.name}")
        else:
            print("Schema created. Set ADMIN_EMAIL and ADMIN_PASSWORD to provision an admin.")


if __name__ == "__main__":
    main()