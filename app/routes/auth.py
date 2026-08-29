from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from app import db
from app.models import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.calendar"))
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email", "").lower().strip()).first()
        if not user or not user.active or not user.check_password(request.form.get("password", "")):
            flash("E-mail, senha ou situação da conta inválidos.", "error")
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


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        new_password = request.form.get("new_password", "")
        password_confirmation = request.form.get("password_confirmation", "")
        current_password = request.form.get("current_password", "")

        if not name:
            flash("Informe seu nome.", "error")
        elif new_password and len(new_password) < 6:
            flash("A nova senha deve ter pelo menos 6 caracteres.", "error")
        elif new_password and not current_user.check_password(current_password):
            flash("A senha atual está incorreta.", "error")
        elif new_password != password_confirmation:
            flash("A confirmação da nova senha não confere.", "error")
        else:
            current_user.name = name
            if new_password:
                current_user.set_password(new_password)
            db.session.commit()
            flash("Sua conta foi atualizada.", "success")
            return redirect(url_for("auth.account"))
    return render_template("account.html")


@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.calendar"))
