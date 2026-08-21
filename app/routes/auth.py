from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from app import db
from app.models import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.calendar"))
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email", "").lower().strip()).first()
        if not user or not user.check_password(request.form.get("password", "")):
            flash("E-mail ou senha inválidos.", "error")
        else:
            login_user(user)
            return redirect(request.args.get("next") or url_for("main.calendar"))
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.calendar"))
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        if User.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "error")
        elif not request.form.get("name") or len(request.form.get("password", "")) < 6:
            flash("Informe seu nome e uma senha com pelo menos 6 caracteres.", "error")
        else:
            user = User(name=request.form["name"].strip(), email=email)
            user.set_password(request.form["password"])
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("main.calendar"))
    return render_template("register.html")


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.calendar"))
