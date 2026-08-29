from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


club_members = db.Table(
    "club_members",
    db.Column("club_id", db.Integer, db.ForeignKey("clubs.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("joined_at", db.DateTime, default=datetime.utcnow, nullable=False),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    active = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    rsvps = db.relationship("RSVP", back_populates="user", cascade="all, delete-orphan")
    clubs = db.relationship("Club", secondary=club_members, back_populates="members")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role in {"admin", "superadmin"}

    @property
    def is_superadmin(self):
        return self.role == "superadmin"

    @property
    def is_active(self):
        return self.active


class Club(db.Model):
    __tablename__ = "clubs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    color_tag = db.Column(db.String(7), nullable=False, default="#e56b4f")
    events = db.relationship("Event", back_populates="club", cascade="all, delete-orphan")
    members = db.relationship("User", secondary=club_members, back_populates="clubs")


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=False)
    book_title = db.Column(db.String(200), nullable=False)
    book_author = db.Column(db.String(160), nullable=False)
    cover_url = db.Column(db.String(500), default="")
    synopsis = db.Column(db.Text, default="")
    event_date = db.Column(db.DateTime, nullable=False, index=True)
    location_type = db.Column(db.String(20), nullable=False, default="presential")
    location_details = db.Column(db.String(500), default="")
    show_rsvp_publicly = db.Column(db.Boolean, default=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    club = db.relationship("Club", back_populates="events")
    rsvps = db.relationship("RSVP", back_populates="event", cascade="all, delete-orphan")

    @property
    def attending_count(self):
        return sum(r.status == "yes" for r in self.rsvps)

    @property
    def declining_count(self):
        return sum(r.status == "no" for r in self.rsvps)


class RSVP(db.Model):
    __tablename__ = "rsvps"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    event = db.relationship("Event", back_populates="rsvps")
    user = db.relationship("User", back_populates="rsvps")
    __table_args__ = (db.UniqueConstraint("event_id", "user_id", name="uq_event_user_rsvp"),)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
