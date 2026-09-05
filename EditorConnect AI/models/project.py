from datetime import datetime, timezone
from database import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), index=True)  # matches PROFESSIONS
    budget = db.Column(db.Float)
    deadline = db.Column(db.Date)

    # status: 'open', 'in_progress', 'completed', 'cancelled'
    status = db.Column(db.String(20), default="open", index=True)

    selected_professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    applications = db.relationship(
        "Application", backref="project", lazy="dynamic", cascade="all, delete-orphan"
    )
    selected_professional = db.relationship("Professional", foreign_keys=[selected_professional_id])

    def application_count(self):
        return self.applications.count()

    def __repr__(self):
        return f"<Project {self.title}>"


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)

    message = db.Column(db.Text)
    proposed_price = db.Column(db.Float)

    # status: 'pending', 'accepted', 'rejected'
    status = db.Column(db.String(20), default="pending", index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("project_id", "professional_id", name="uq_project_professional"),
    )

    def __repr__(self):
        return f"<Application project={self.project_id} pro={self.professional_id}>"
