from database import db
from models.notification import Notification


def notify(user_id, type_, title, body=None, link=None):
    """Create a notification for a user. Call db.session.commit() after."""
    n = Notification(user_id=user_id, type=type_, title=title, body=body, link=link)
    db.session.add(n)
    return n
