from calendar import monthrange
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Event, RSVP


main_bp = Blueprint("main", __name__)

MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


@main_bp.route("/")
def calendar():
    selected = request.args.get("month", datetime.now().strftime("%Y-%m"))
    try:
        month_start = datetime.strptime(selected, "%Y-%m")
    except ValueError:
        month_start = datetime.now().replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)
    previous_month = month_start
    if previous_month.month == 1:
        previous_month = previous_month.replace(year=previous_month.year - 1, month=12)
    else:
        previous_month = previous_month.replace(month=previous_month.month - 1)
    next_month = month_end
    events = Event.query.filter(Event.event_date >= month_start, Event.event_date < month_end).order_by(Event.event_date).all()
    upcoming = Event.query.filter(Event.event_date >= datetime.now()).order_by(Event.event_date).limit(6).all()
    event_days = {}
    for event in events:
        event_days.setdefault(event.event_date.day, []).append(event)
    return render_template("calendar.html", events=events, upcoming=upcoming, event_days=event_days, selected=month_start.strftime("%Y-%m"), month_label=MONTH_NAMES[month_start.month - 1], year=month_start.year, month_start=month_start, now=datetime.now(), days_in_month=monthrange(month_start.year, month_start.month)[1], previous_month=previous_month.strftime("%Y-%m"), next_month=next_month.strftime("%Y-%m"))


@main_bp.route("/events/<int:event_id>")
def event_detail(event_id):
    event = db.get_or_404(Event, event_id)
    return render_template("event_detail.html", event=event)


@main_bp.post("/events/<int:event_id>/rsvp")
@login_required
def rsvp(event_id):
    event = db.get_or_404(Event, event_id)
    status = request.form.get("status")
    if status not in {"yes", "no"}:
        abort(400)
    response = RSVP.query.filter_by(event_id=event.id, user_id=current_user.id).first()
    if response is None:
        response = RSVP(event=event, user=current_user, status=status)
        db.session.add(response)
    else:
        response.status = status
    db.session.commit()
    flash("Sua resposta foi atualizada.", "success")
    return redirect(url_for("main.event_detail", event_id=event.id))
