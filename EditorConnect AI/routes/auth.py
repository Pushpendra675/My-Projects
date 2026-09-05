from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from database import db
from models.user import User
from models.professional import Professional
from config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.name}.", "success")
            next_url = request.args.get("next")
            if next_url:
                return redirect(next_url)
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            if user.is_professional:
                return redirect(url_for("professional.dashboard"))
            return redirect(url_for("client.dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "client")
        profession = request.form.get("profession", "")

        if role not in ("client", "professional"):
            role = "client"

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("auth/register.html", professions=Config.PROFESSIONS)

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html", professions=Config.PROFESSIONS)

        user = User(name=name, email=email, phone=phone, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        if role == "professional":
            pro = Professional(
                user_id=user.id,
                name=name,
                profession=profession or "Content Creator",
                email=email,
                phone=phone,
                is_approved=False,
            )
            db.session.add(pro)

        db.session.commit()
        login_user(user)
        flash("Account created. Welcome to EditorConnect AI.", "success")

        if role == "professional":
            return redirect(url_for("professional.dashboard"))
        return redirect(url_for("client.dashboard"))

    return render_template("auth/register.html", professions=Config.PROFESSIONS)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
