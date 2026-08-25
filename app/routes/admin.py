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
@admin_required
def users():
    query = request.args.get("q", "").strip()
    users_query = User.query
    if query:
        search = f"%{query}%"
        users_query = users_query.filter(or_(User.name.ilike(search), User.email.ilike(search)))
    found_users = users_query.order_by(User.name).all()
    administrators = User.query.filter_by(role="admin").order_by(User.name).all()
    return render_template("admin_users.html", users=found_users, administrators=administrators, query=query)


@admin_bp.post("/users/<int:user_id>/role")
@admin_required
def update_user_role(user_id):
    user = db.get_or_404(User, user_id)
    role = request.form.get("role")
    query = request.form.get("q", "")
    if role not in {"admin", "member"}:
        abort(400)
    if role == "member" and user.is_admin:
        if user.id == current_user.id:
            flash("Você não pode remover seu próprio acesso de administrador.", "error")
            return redirect(url_for("admin.users", q=query))
        if User.query.filter_by(role="admin").count() <= 1:
            flash("O grupo precisa manter pelo menos um administrador.", "error")
            return redirect(url_for("admin.users", q=query))
    user.role = role
    db.session.commit()
    flash(f"Acesso de {user.name} atualizado.", "success")
    return redirect(url_for("admin.users", q=query))


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
