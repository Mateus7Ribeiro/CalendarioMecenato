from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Club, Event


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
