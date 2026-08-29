from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app import db
from app.models import Club, Event, User


admin_bp = Blueprint("admin", __name__)


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def superadmin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_superadmin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route("/")
@admin_required
def dashboard():
    return render_template("admin_dashboard.html", events=Event.query.order_by(Event.event_date.desc()).all(), clubs=Club.query.order_by(Club.name).all())


@admin_bp.route("/clubs")
@admin_required
def clubs():
    return render_template("admin_clubs.html", clubs=Club.query.order_by(Club.name).all())


@admin_bp.route("/clubs/new", methods=["GET", "POST"])
@admin_required
def new_club():
    if request.method == "POST":
        club = _club_from_form(Club())
        db.session.add(club)
        db.session.commit()
        flash("Clube criado.", "success")
        return redirect(url_for("admin.clubs"))
    return render_template("admin_club_form.html", club=None, title="Novo clube")


@admin_bp.route("/clubs/<int:club_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_club(club_id):
    club = db.get_or_404(Club, club_id)
    if request.method == "POST":
        _club_from_form(club)
        db.session.commit()
        flash("Clube atualizado.", "success")
        return redirect(url_for("admin.clubs"))
    return render_template("admin_club_form.html", club=club, title="Editar clube")


@admin_bp.post("/clubs/<int:club_id>/delete")
@admin_required
def delete_club(club_id):
    club = db.get_or_404(Club, club_id)
    if club.events:
        flash("Este clube não pode ser apagado porque possui encontros cadastrados.", "error")
        return redirect(url_for("admin.clubs"))
    db.session.delete(club)
    db.session.commit()
    flash("Clube apagado.", "success")
    return redirect(url_for("admin.clubs"))


@admin_bp.route("/users")
@superadmin_required
def users():
    query = request.args.get("q", "").strip()
    users_query = User.query
    if query:
        search = f"%{query}%"
        users_query = users_query.filter(or_(User.name.ilike(search), User.email.ilike(search)))
    found_users = users_query.order_by(User.name).all()
    return render_template("admin_users.html", users=found_users, query=query)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@superadmin_required
def new_user():
    if request.method == "POST":
        if _save_user_from_form(User()):
            flash("Usuário criado.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin_user_form.html", user=None, title="Novo usuário")


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@superadmin_required
def edit_user(user_id):
    user = db.get_or_404(User, user_id)
    if request.method == "POST":
        if _save_user_from_form(user):
            flash("Usuário atualizado.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin_user_form.html", user=user, title="Editar usuário")


@admin_bp.post("/users/<int:user_id>/status")
@superadmin_required
def update_user_status(user_id):
    user = db.get_or_404(User, user_id)
    active = request.form.get("active") == "1"
    if not active and user.id == current_user.id:
        flash("Você não pode inativar sua própria conta.", "error")
        return redirect(url_for("admin.users"))
    if not active and user.is_superadmin and User.query.filter_by(role="superadmin", active=True).count() <= 1:
        flash("O site precisa manter pelo menos um super administrador ativo.", "error")
        return redirect(url_for("admin.users"))
    user.active = active
    db.session.commit()
    flash(f"Usuário {user.name} {'ativado' if active else 'inativado'}.", "success")
    return redirect(url_for("admin.users"))


def _save_user_from_form(user):
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").lower().strip()
    password = request.form.get("password", "")
    if not name or not email or (user.id is None and len(password) < 6):
        flash("Informe nome, e-mail e uma senha com pelo menos 6 caracteres para novos usuários.", "error")
        return False
    duplicate = User.query.filter(User.email == email, User.id != user.id).first()
    if duplicate:
        flash("Este e-mail já está cadastrado.", "error")
        return False
    user.name = name
    user.email = email
    requested_role = request.form.get("role", "member")
    if requested_role not in {"admin", "member"}:
        abort(400)
    if user.id != current_user.id and user.role != "superadmin":
        user.role = requested_role
    requested_active = request.form.get("active") == "1" if user.id is not None else True
    if user.id == current_user.id and not requested_active:
        flash("Você não pode inativar sua própria conta.", "error")
        return False
    if user.id != current_user.id and user.role == "superadmin" and not requested_active and User.query.filter_by(role="superadmin", active=True).count() <= 1:
        flash("O site precisa manter pelo menos um super administrador ativo.", "error")
        return False
    user.active = requested_active
    if password:
        if len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "error")
            return False
        user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return True


@admin_bp.route("/events/new", methods=["GET", "POST"])
@admin_required
def new_event():
    clubs = Club.query.order_by(Club.name).all()
    if request.method == "POST":
        event = _event_from_form(Event(created_by=current_user.id))
        db.session.add(event)
        db.session.commit()
        flash("Encontro criado.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_form.html", event=None, clubs=clubs, title="Novo encontro")


@admin_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_event(event_id):
    event = db.get_or_404(Event, event_id)
    if request.method == "POST":
        _event_from_form(event)
        db.session.commit()
        flash("Encontro atualizado.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_form.html", event=event, clubs=Club.query.order_by(Club.name).all(), title="Editar encontro")


@admin_bp.post("/events/<int:event_id>/delete")
@admin_required
def delete_event(event_id):
    db.session.delete(db.get_or_404(Event, event_id))
    db.session.commit()
    flash("Encontro excluído.", "success")
    return redirect(url_for("admin.dashboard"))


def _event_from_form(event):
    event.club_id = int(request.form["club_id"])
    event.book_title = request.form["book_title"].strip()
    event.book_author = request.form["book_author"].strip()
    event.cover_url = request.form.get("cover_url", "").strip()
    event.synopsis = request.form.get("synopsis", "").strip()
    event.event_date = datetime.fromisoformat(request.form["event_date"])
    event.location_type = request.form["location_type"]
    event.location_details = request.form.get("location_details", "").strip()
    event.show_rsvp_publicly = "show_rsvp_publicly" in request.form
    return event


def _club_from_form(club):
    club.name = request.form["name"].strip()
    club.description = request.form.get("description", "").strip()
    club.color_tag = request.form.get("color_tag", "#e56b4f").strip()
    return club
