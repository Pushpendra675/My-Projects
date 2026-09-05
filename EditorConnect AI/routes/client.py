import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from database import db
from models.project import Project, Application
from models.professional import Professional
from models.hire import Hire
from routes import notify
from config import Config

client_bp = Blueprint("client", __name__)


def client_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_client:
            flash("This area is for client accounts only.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return wrapped


@client_bp.route("/client-dashboard")
@login_required
@client_required
def dashboard():
    my_projects = current_user.projects.order_by(Project.created_at.desc()).limit(5).all()
    active_hires = Hire.query.filter_by(client_id=current_user.id, status="accepted").count()
    pending_hires = Hire.query.filter_by(client_id=current_user.id, status="pending").count()
    open_count = current_user.projects.filter_by(status="open").count()
    in_progress_count = current_user.projects.filter_by(status="in_progress").count()
    completed_count = current_user.projects.filter_by(status="completed").count()

    return render_template(
        "client/dashboard.html",
        my_projects=my_projects,
        active_hires=active_hires,
        pending_hires=pending_hires,
        open_count=open_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
    )


@client_bp.route("/client/projects")
@login_required
@client_required
def my_projects():
    projects = current_user.projects.order_by(Project.created_at.desc()).all()
    return render_template("client/my_projects.html", projects=projects)


@client_bp.route("/client/projects/new", methods=["GET", "POST"])
@login_required
@client_required
def create_project():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        budget = request.form.get("budget", type=float)
        deadline_raw = request.form.get("deadline", "")

        if not title or not description:
            flash("Title and description are required.", "error")
            return render_template("client/project_form.html", professions=Config.PROFESSIONS, project=None)

        deadline = None
        if deadline_raw:
            try:
                deadline = datetime.strptime(deadline_raw, "%Y-%m-%d").date()
            except ValueError:
                pass

        project = Project(
            client_id=current_user.id,
            title=title,
            description=description,
            category=category,
            budget=budget,
            deadline=deadline,
            status="open",
        )
        db.session.add(project)
        db.session.commit()
        flash("Project created and published.", "success")
        return redirect(url_for("client.my_projects"))

    return render_template("client/project_form.html", professions=Config.PROFESSIONS, project=None)


@client_bp.route("/client/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
@client_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.client_id != current_user.id:
        flash("You can only edit your own projects.", "error")
        return redirect(url_for("client.my_projects"))

    if request.method == "POST":
        project.title = request.form.get("title", "").strip()
        project.description = request.form.get("description", "").strip()
        project.category = request.form.get("category", "")
        project.budget = request.form.get("budget", type=float)
        deadline_raw = request.form.get("deadline", "")
        if deadline_raw:
            try:
                project.deadline = datetime.strptime(deadline_raw, "%Y-%m-%d").date()
            except ValueError:
                pass

        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("client.my_projects"))

    return render_template("client/project_form.html", professions=Config.PROFESSIONS, project=project)


@client_bp.route("/client/projects/<int:project_id>/delete", methods=["POST"])
@login_required
@client_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.client_id != current_user.id:
        flash("You can only delete your own projects.", "error")
        return redirect(url_for("client.my_projects"))

    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "success")
    return redirect(url_for("client.my_projects"))


@client_bp.route("/client/projects/<int:project_id>")
@login_required
@client_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if project.client_id != current_user.id:
        flash("You can only view your own project details.", "error")
        return redirect(url_for("client.my_projects"))
    applications = project.applications.order_by(Application.created_at.desc()).all()
    return render_template("client/project_detail.html", project=project, applications=applications)


@client_bp.route("/client/applications/<int:application_id>/select", methods=["POST"])
@login_required
@client_required
def select_applicant(application_id):
    application = Application.query.get_or_404(application_id)
    project = application.project
    if project.client_id != current_user.id:
        flash("Not authorized.", "error")
        return redirect(url_for("client.my_projects"))

    application.status = "accepted"
    project.status = "in_progress"
    project.selected_professional_id = application.professional_id

    for other in project.applications:
        if other.id != application.id and other.status == "pending":
            other.status = "rejected"
            notify(
                other.professional.user_id, "application_rejected",
                "Application not selected",
                f"The client chose another professional for '{project.title}'.",
                url_for("professional.browse_projects"),
            )

    notify(
        application.professional.user_id, "application_accepted",
        "Your application was accepted!",
        f"You were selected for '{project.title}'.",
        url_for("professional.accepted_projects"),
    )
    db.session.commit()
    flash(f"{application.professional.name} has been selected for this project.", "success")
    return redirect(url_for("client.project_detail", project_id=project.id))


@client_bp.route("/client/hire/<int:professional_id>", methods=["POST"])
@login_required
@client_required
def hire_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)

    existing = Hire.query.filter_by(
        client_id=current_user.id, professional_id=professional.id, status="pending"
    ).first()
    if existing:
        flash("You already have a pending hire request with this professional.", "info")
        return redirect(url_for("main.professional_profile", professional_id=professional.id))

    message = request.form.get("message", "").strip()
    budget = request.form.get("budget", type=float)

    hire = Hire(
        client_id=current_user.id,
        professional_id=professional.id,
        message=message,
        budget=budget,
        status="pending",
    )
    db.session.add(hire)
    notify(
        professional.user_id, "hire_request",
        f"New hire request from {current_user.name}",
        message or "You have a new hire request.",
        url_for("professional.dashboard"),
    )
    db.session.commit()
    flash(f"Hire request sent to {professional.name}.", "success")
    return redirect(url_for("main.professional_profile", professional_id=professional.id))


@client_bp.route("/client/hired-professionals")
@login_required
@client_required
def hired_professionals():
    hires = Hire.query.filter_by(client_id=current_user.id).order_by(Hire.created_at.desc()).all()
    return render_template("client/hired_professionals.html", hires=hires)


@client_bp.route("/client/profile", methods=["GET", "POST"])
@login_required
@client_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.phone = request.form.get("phone", current_user.phone)

        file = request.files.get("avatar")
        if file and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext in Config.ALLOWED_IMAGE_EXTENSIONS:
                filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                path = os.path.join(Config.PROFILE_UPLOAD_FOLDER, filename)
                file.save(path)
                current_user.avatar = filename

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("client.profile"))

    return render_template("client/profile.html")


@client_bp.route("/client/settings", methods=["GET", "POST"])
@login_required
@client_required
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            if not current_user.check_password(current_pw):
                flash("Current password is incorrect.", "error")
            elif len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "error")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash("Password changed successfully.", "success")
        elif action == "toggle_dark_mode":
            current_user.dark_mode = not current_user.dark_mode
            db.session.commit()
        return redirect(url_for("client.settings"))

    return render_template("client/settings.html")
