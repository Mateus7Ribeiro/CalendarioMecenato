from flask import Flask
from sqlalchemy import inspect, text
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import Config


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Entre para participar do calendário."
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        from app.models import Club, Event, User
        if app.config["AUTO_CREATE_DB"]:
            db.create_all()
        _ensure_user_active_column()
        if app.config["SEED_DEMO_DATA"]:
            _seed_demo_data(User, Club, Event)

    return app


def _ensure_user_active_column():
    """Add the account status column to databases created before this feature."""
    columns = {column["name"] for column in inspect(db.engine).get_columns("users")}
    if "active" not in columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1"))


def _seed_demo_data(User, Club, Event):
    if Club.query.count():
        return

    admin = User(
        name="Admin Mecenato",
        email="admin@mecenato.local",
        role="admin",
    )
    admin.set_password("admin123")
    club = Club(
        name="Clube Mecenato",
        description="Leituras que viram conversa e encontro.",
        color_tag="#e56b4f",
    )
    db.session.add_all([admin, club])
    db.session.flush()
    db.session.add(
        Event(
            club_id=club.id,
            book_title="Torto Arado",
            book_author="Itamar Vieira Junior",
            cover_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500&q=80",
            synopsis="Uma história de terra, memória e laços que atravessam gerações.",
            event_date=__import__("datetime").datetime(2026, 9, 12, 19, 30),
            location_type="presential",
            location_details="Casa das Letras, Rua das Flores, 120",
            created_by=admin.id,
        )
    )
    db.session.commit()
