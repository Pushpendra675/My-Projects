from datetime import datetime, timezone
from database import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # type: 'hire_request', 'hire_accepted', 'hire_declined', 'new_message',
    #       'project_application', 'application_accepted', 'application_rejected', 'system'
    type = db.Column(db.String(30), nullable=False, default="system")
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text)
    link = db.Column(db.String(255))  # url_for target to navigate to

    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Notification {self.type} for user={self.user_id}>"
