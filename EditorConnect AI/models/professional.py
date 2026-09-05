from datetime import datetime, timezone
from database import db


class Professional(db.Model):
    __tablename__ = "professionals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    name = db.Column(db.String(120), nullable=False)
    profession = db.Column(db.String(80), nullable=False, index=True)
    city = db.Column(db.String(100), index=True)
    experience = db.Column(db.Integer, default=0)  # years
    price = db.Column(db.Float, default=0.0)  # starting price
    rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    skills = db.Column(db.String(500))  # comma-separated
    profile_image = db.Column(db.String(255), default="default-avatar.png")
    email = db.Column(db.String(150))
    phone = db.Column(db.String(30))

    is_available = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)  # admin approval
    is_featured = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    portfolio_items = db.relationship(
        "PortfolioItem", backref="professional", lazy="dynamic", cascade="all, delete-orphan"
    )
    applications = db.relationship(
        "Application", backref="professional", lazy="dynamic", cascade="all, delete-orphan"
    )
    hires = db.relationship(
        "Hire", backref="professional", lazy="dynamic", cascade="all, delete-orphan"
    )

    def skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def __repr__(self):
        return f"<Professional {self.name} ({self.profession})>"


class PortfolioItem(db.Model):
    __tablename__ = "portfolio_items"

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)

    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    media_type = db.Column(db.String(10), default="image")  # 'image' or 'video'
    file_path = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PortfolioItem {self.title}>"
