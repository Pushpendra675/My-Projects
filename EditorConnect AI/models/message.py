from datetime import datetime, timezone
from database import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_one_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_two_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_message_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_one = db.relationship("User", foreign_keys=[user_one_id])
    user_two = db.relationship("User", foreign_keys=[user_two_id])
    messages = db.relationship(
        "Message", backref="conversation", lazy="dynamic",
        cascade="all, delete-orphan", order_by="Message.created_at"
    )

    __table_args__ = (
        db.UniqueConstraint("user_one_id", "user_two_id", name="uq_conversation_pair"),
    )

    def other_user(self, current_user_id):
        return self.user_two if self.user_one_id == current_user_id else self.user_one

    def last_message(self):
        return self.messages.order_by(Message.created_at.desc()).first()

    def unread_count_for(self, user_id):
        return self.messages.filter(
            Message.sender_id != user_id, Message.is_read.is_(False)
        ).count()

    def __repr__(self):
        return f"<Conversation {self.user_one_id}<->{self.user_two_id}>"


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<Message from={self.sender_id}>"
