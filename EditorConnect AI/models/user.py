from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)

    # role: 'client', 'professional', 'admin'
    role = db.Column(db.String(20), nullable=False, default="client")

    is_active_account = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    dark_mode = db.Column(db.Boolean, default=True)
    avatar = db.Column(db.String(255), default="default-avatar.png")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    professional_profile = db.relationship(
        "Professional", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    projects = db.relationship(
        "Project", backref="client", lazy="dynamic", cascade="all, delete-orphan",
        foreign_keys="Project.client_id"
    )
    notifications = db.relationship(
        "Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_professional(self):
        return self.role == "professional"

    @property
    def is_client(self):
        return self.role == "client"

    def unread_notification_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
