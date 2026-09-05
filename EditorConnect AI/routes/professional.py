import os
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from database import db
from models.project import Project, Application
from models.hire import Hire
from routes import notify
from config import Config

professional_bp = Blueprint("professional", __name__)


def professional_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_professional:
            flash("This area is for professional accounts only.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return wrapped


def get_profile_or_404():
    pro = current_user.professional_profile
    if pro is None:
        flash("Professional profile not found.", "error")
    return pro


@professional_bp.route("/professional-dashboard")
@login_required
@professional_required
def dashboard():
    pro = get_profile_or_404()
    pending_hires = Hire.query.filter_by(professional_id=pro.id, status="pending").all() if pro else []
    accepted_projects_count = Application.query.filter_by(
        professional_id=pro.id, status="accepted"
    ).count() if pro else 0
    pending_applications = Application.query.filter_by(
        professional_id=pro.id, status="pending"
    ).count() if pro else 0
    portfolio_count = pro.portfolio_items.count() if pro else 0

    return render_template(
        "professional/dashboard.html",
        professional=pro,
        pending_hires=pending_hires,
        accepted_projects_count=accepted_projects_count,
        pending_applications=pending_applications,
        portfolio_count=portfolio_count,
    )


@professional_bp.route("/professional/browse-projects")
@login_required
@professional_required
def browse_projects():
    pro = get_profile_or_404()
    category = request.args.get("category", "")
    search = request.args.get("q", "").strip()

    query = Project.query.filter_by(status="open")
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Project.title.ilike(f"%{search}%"))

    projects = query.order_by(Project.created_at.desc()).all()
    applied_ids = {a.project_id for a in pro.applications} if pro else set()

    return render_template(
        "professional/browse_projects.html",
        projects=projects,
        professions=Config.PROFESSIONS,
        filters=request.args,
        applied_ids=applied_ids,
    )


@professional_bp.route("/professional/apply/<int:project_id>", methods=["GET", "POST"])
@login_required
@professional_required
def apply_project(project_id):
    pro = get_profile_or_404()
    project = Project.query.get_or_404(project_id)

    existing = Application.query.filter_by(project_id=project.id, professional_id=pro.id).first()
    if existing:
        flash("You already applied to this project.", "info")
        return redirect(url_for("professional.browse_projects"))

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        proposed_price = request.form.get("proposed_price", type=float)

        application = Application(
            project_id=project.id,
            professional_id=pro.id,
            message=message,
            proposed_price=proposed_price,
            status="pending",
        )
        db.session.add(application)
        notify(
            project.client_id, "project_application",
            f"New application from {pro.name}",
            f"{pro.name} applied to '{project.title}'.",
            url_for("client.project_detail", project_id=project.id),
        )
        db.session.commit()
        flash("Application submitted.", "success")
        return redirect(url_for("professional.browse_projects"))

    return render_template("professional/apply_project.html", project=project)


@professional_bp.route("/professional/accepted-projects")
@login_required
@professional_required
def accepted_projects():
    pro = get_profile_or_404()
    applications = Application.query.filter_by(
        professional_id=pro.id, status="accepted"
    ).order_by(Application.created_at.desc()).all() if pro else []
    return render_template("professional/accepted_projects.html", applications=applications)


@professional_bp.route("/professional/hires/<int:hire_id>/respond", methods=["POST"])
@login_required
@professional_required
def respond_hire(hire_id):
    pro = get_profile_or_404()
    hire = Hire.query.get_or_404(hire_id)
    if hire.professional_id != pro.id:
        flash("Not authorized.", "error")
        return redirect(url_for("professional.dashboard"))

    action = request.form.get("action")
    if action == "accept":
        hire.status = "accepted"
        notify(
            hire.client_id, "hire_accepted",
            f"{pro.name} accepted your hire request",
            "You can now message them to get started.",
            url_for("client.hired_professionals"),
        )
        flash("Hire request accepted.", "success")
    elif action == "decline":
        hire.status = "declined"
        notify(
            hire.client_id, "hire_declined",
            f"{pro.name} declined your hire request",
            None,
            url_for("client.hired_professionals"),
        )
        flash("Hire request declined.", "info")

    db.session.commit()
    return redirect(url_for("professional.dashboard"))


@professional_bp.route("/professional/portfolio")
@login_required
@professional_required
def portfolio():
    from models.professional import PortfolioItem

    pro = get_profile_or_404()
    items = pro.portfolio_items.order_by(PortfolioItem.created_at.desc()).all() if pro else []
    return render_template("professional/portfolio.html", professional=pro, items=items)


@professional_bp.route("/professional/portfolio/add", methods=["POST"])
@login_required
@professional_required
def add_portfolio_item():
    from models.professional import PortfolioItem

    pro = get_profile_or_404()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    file = request.files.get("file")

    if not file or not file.filename:
        flash("Please choose a file to upload.", "error")
        return redirect(url_for("professional.portfolio"))

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext in Config.ALLOWED_IMAGE_EXTENSIONS:
        media_type = "image"
    elif ext in Config.ALLOWED_VIDEO_EXTENSIONS:
        media_type = "video"
    else:
        flash("Unsupported file type.", "error")
        return redirect(url_for("professional.portfolio"))

    filename = secure_filename(f"pro_{pro.id}_{file.filename}")
    path = os.path.join(Config.PORTFOLIO_UPLOAD_FOLDER, filename)
    file.save(path)

    item = PortfolioItem(
        professional_id=pro.id,
        title=title,
        description=description,
        media_type=media_type,
        file_path=filename,
    )
    db.session.add(item)
    db.session.commit()
    flash("Portfolio item added.", "success")
    return redirect(url_for("professional.portfolio"))


@professional_bp.route("/professional/portfolio/<int:item_id>/delete", methods=["POST"])
@login_required
@professional_required
def delete_portfolio_item(item_id):
    from models.professional import PortfolioItem

    pro = get_profile_or_404()
    item = PortfolioItem.query.get_or_404(item_id)
    if item.professional_id != pro.id:
        flash("Not authorized.", "error")
        return redirect(url_for("professional.portfolio"))

    db.session.delete(item)
    db.session.commit()
    flash("Portfolio item removed.", "success")
    return redirect(url_for("professional.portfolio"))


@professional_bp.route("/professional/profile/edit", methods=["GET", "POST"])
@login_required
@professional_required
def edit_profile():
    pro = get_profile_or_404()

    if request.method == "POST":
        pro.name = request.form.get("name", pro.name).strip()
        pro.profession = request.form.get("profession", pro.profession)
        pro.city = request.form.get("city", pro.city)
        pro.experience = request.form.get("experience", type=int) or pro.experience
        pro.price = request.form.get("price", type=float) or pro.price
        pro.bio = request.form.get("bio", pro.bio)
        pro.skills = request.form.get("skills", pro.skills)
        pro.phone = request.form.get("phone", pro.phone)
        pro.is_available = request.form.get("is_available") == "on"

        file = request.files.get("profile_image")
        if file and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext in Config.ALLOWED_IMAGE_EXTENSIONS:
                filename = secure_filename(f"pro_{pro.id}_{file.filename}")
                path = os.path.join(Config.PROFILE_UPLOAD_FOLDER, filename)
                file.save(path)
                pro.profile_image = filename

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("professional.edit_profile"))

    return render_template("professional/edit_profile.html", professional=pro, professions=Config.PROFESSIONS)


@professional_bp.route("/professional/settings", methods=["GET", "POST"])
@login_required
@professional_required
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
        return redirect(url_for("professional.settings"))

    return render_template("professional/settings.html")
