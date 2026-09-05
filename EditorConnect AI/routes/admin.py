from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from database import db
from models.user import User
from models.professional import Professional
from models.project import Project
from models.hire import Hire

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access only.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return wrapped


@admin_bp.route("/admin")
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_clients = User.query.filter_by(role="client").count()
    total_professionals = User.query.filter_by(role="professional").count()
    pending_approvals = Professional.query.filter_by(is_approved=False).count()
    total_projects = Project.query.count()
    open_projects = Project.query.filter_by(status="open").count()
    completed_projects = Project.query.filter_by(status="completed").count()
    total_hires = Hire.query.count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_clients=total_clients,
        total_professionals=total_professionals,
        pending_approvals=pending_approvals,
        total_projects=total_projects,
        open_projects=open_projects,
        completed_projects=completed_projects,
        total_hires=total_hires,
        recent_users=recent_users,
    )


@admin_bp.route("/admin/users")
@login_required
@admin_required
def manage_users():
    role_filter = request.args.get("role", "")
    query = User.query
    if role_filter in ("client", "professional", "admin"):
        query = query.filter_by(role=role_filter)
    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/manage_users.html", users=users, role_filter=role_filter)


@admin_bp.route("/admin/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't deactivate your own account.", "error")
        return redirect(url_for("admin.manage_users"))
    user.is_active_account = not user.is_active_account
    db.session.commit()
    flash(f"{user.name}'s account is now {'active' if user.is_active_account else 'suspended'}.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't delete your own account.", "error")
        return redirect(url_for("admin.manage_users"))
    db.session.delete(user)
    db.session.commit()
    flash("Account removed.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/admin/professionals")
@login_required
@admin_required
def manage_professionals():
    status_filter = request.args.get("status", "")
    query = Professional.query
    if status_filter == "pending":
        query = query.filter_by(is_approved=False)
    elif status_filter == "approved":
        query = query.filter_by(is_approved=True)
    professionals = query.order_by(Professional.created_at.desc()).all()
    return render_template("admin/manage_professionals.html", professionals=professionals, status_filter=status_filter)


@admin_bp.route("/admin/professionals/<int:pro_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_professional(pro_id):
    pro = Professional.query.get_or_404(pro_id)
    pro.is_approved = True
    db.session.commit()
    flash(f"{pro.name} approved and now visible in listings.", "success")
    return redirect(url_for("admin.manage_professionals"))


@admin_bp.route("/admin/professionals/<int:pro_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_professional(pro_id):
    pro = Professional.query.get_or_404(pro_id)
    pro.is_approved = False
    db.session.commit()
    flash(f"{pro.name}'s listing has been hidden.", "info")
    return redirect(url_for("admin.manage_professionals"))


@admin_bp.route("/admin/professionals/<int:pro_id>/remove", methods=["POST"])
@login_required
@admin_required
def remove_professional(pro_id):
    """Remove a fake / fraudulent professional account entirely."""
    pro = Professional.query.get_or_404(pro_id)
    user = pro.user
    db.session.delete(pro)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash("Professional account removed.", "success")
    return redirect(url_for("admin.manage_professionals"))


@admin_bp.route("/admin/projects")
@login_required
@admin_required
def manage_projects():
    status_filter = request.args.get("status", "")
    query = Project.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    projects = query.order_by(Project.created_at.desc()).all()
    return render_template("admin/manage_projects.html", projects=projects, status_filter=status_filter)


@admin_bp.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash("Project removed.", "success")
    return redirect(url_for("admin.manage_projects"))


@admin_bp.route("/admin/analytics")
@login_required
@admin_required
def analytics():
    from sqlalchemy import func

    users_by_role = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
    professionals_by_profession = (
        db.session.query(Professional.profession, func.count(Professional.id))
        .group_by(Professional.profession)
        .all()
    )
    projects_by_status = db.session.query(Project.status, func.count(Project.id)).group_by(Project.status).all()

    return render_template(
        "admin/analytics.html",
        users_by_role=users_by_role,
        professionals_by_profession=professionals_by_profession,
        projects_by_status=projects_by_status,
    )
