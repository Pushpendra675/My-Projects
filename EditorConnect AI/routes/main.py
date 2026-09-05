from flask import Blueprint, render_template, request
from flask_login import current_user

from models.professional import Professional, PortfolioItem
from models.project import Project
from config import Config

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    featured = (
        Professional.query.filter_by(is_approved=True)
        .order_by(Professional.rating.desc())
        .limit(6)
        .all()
    )
    open_projects_count = Project.query.filter_by(status="open").count()
    pro_count = Professional.query.filter_by(is_approved=True).count()
    return render_template(
        "landing.html",
        featured=featured,
        professions=Config.PROFESSIONS,
        open_projects_count=open_projects_count,
        pro_count=pro_count,
    )


@main_bp.route("/professionals")
def professionals():
    query = Professional.query.filter_by(is_approved=True)

    search = request.args.get("q", "").strip()
    profession = request.args.get("profession", "")
    city = request.args.get("city", "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    min_rating = request.args.get("min_rating", type=float)
    min_experience = request.args.get("min_experience", type=int)
    availability = request.args.get("availability", "")
    sort = request.args.get("sort", "rating")

    if search:
        like = f"%{search}%"
        query = query.filter(
            (Professional.name.ilike(like)) | (Professional.skills.ilike(like))
        )
    if profession:
        query = query.filter_by(profession=profession)
    if city:
        query = query.filter(Professional.city.ilike(f"%{city}%"))
    if min_price is not None:
        query = query.filter(Professional.price >= min_price)
    if max_price is not None:
        query = query.filter(Professional.price <= max_price)
    if min_rating is not None:
        query = query.filter(Professional.rating >= min_rating)
    if min_experience is not None:
        query = query.filter(Professional.experience >= min_experience)
    if availability == "available":
        query = query.filter_by(is_available=True)

    if sort == "price_low":
        query = query.order_by(Professional.price.asc())
    elif sort == "price_high":
        query = query.order_by(Professional.price.desc())
    elif sort == "experience":
        query = query.order_by(Professional.experience.desc())
    else:
        query = query.order_by(Professional.rating.desc())

    results = query.all()

    return render_template(
        "professionals.html",
        professionals=results,
        professions=Config.PROFESSIONS,
        filters=request.args,
    )


@main_bp.route("/professional/<int:professional_id>")
def professional_profile(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    portfolio_items = professional.portfolio_items.order_by(PortfolioItem.created_at.desc()).all()
    already_hired = False
    if current_user.is_authenticated and current_user.is_client:
        from models.hire import Hire
        already_hired = Hire.query.filter_by(
            client_id=current_user.id,
            professional_id=professional.id,
            status="pending",
        ).first() is not None

    return render_template(
        "professional_profile.html",
        professional=professional,
        portfolio_items=portfolio_items,
        already_hired=already_hired,
    )


@main_bp.route("/projects")
def projects():
    query = Project.query.filter_by(status="open")

    category = request.args.get("category", "")
    search = request.args.get("q", "").strip()

    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Project.title.ilike(f"%{search}%"))

    results = query.order_by(Project.created_at.desc()).all()

    applied_project_ids = set()
    if current_user.is_authenticated and current_user.is_professional:
        pro = current_user.professional_profile
        if pro:
            applied_project_ids = {a.project_id for a in pro.applications}

    return render_template(
        "projects.html",
        projects=results,
        professions=Config.PROFESSIONS,
        filters=request.args,
        applied_project_ids=applied_project_ids,
    )
