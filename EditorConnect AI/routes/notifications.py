from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from database import db
from models.notification import Notification

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications")
@login_required
def index():
    items = current_user.notifications.order_by(Notification.created_at.desc()).all()
    unread = [n for n in items if not n.is_read]
    for n in unread:
        n.is_read = True
    if unread:
        db.session.commit()
    return render_template("notifications.html", notifications=items)


@notifications_bp.route("/notifications/<int:notification_id>/go")
@login_required
def go(notification_id):
    n = Notification.query.get_or_404(notification_id)
    if n.user_id != current_user.id:
        return redirect(url_for("notifications.index"))
    if not n.is_read:
        n.is_read = True
        db.session.commit()
    return redirect(n.link or url_for("notifications.index"))
