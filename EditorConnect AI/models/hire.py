from datetime import datetime, timezone
from database import db


class Hire(db.Model):
    __tablename__ = "hires"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)

    message = db.Column(db.Text)
    budget = db.Column(db.Float)

    # status: 'pending', 'accepted', 'declined', 'completed'
    status = db.Column(db.String(20), default="pending", index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    client = db.relationship("User", foreign_keys=[client_id])

    def __repr__(self):
        return f"<Hire client={self.client_id} pro={self.professional_id} status={self.status}>"
