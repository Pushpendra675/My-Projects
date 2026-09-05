from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_

from database import db
from models.user import User
from models.message import Conversation, Message
from routes import notify

messages_bp = Blueprint("messages", __name__)


def get_or_create_conversation(user_a_id, user_b_id):
    lo, hi = sorted([user_a_id, user_b_id])
    convo = Conversation.query.filter_by(user_one_id=lo, user_two_id=hi).first()
    if not convo:
        convo = Conversation(user_one_id=lo, user_two_id=hi)
        db.session.add(convo)
        db.session.commit()
    return convo


@messages_bp.route("/messages")
@login_required
def conversations():
    convos = Conversation.query.filter(
        or_(Conversation.user_one_id == current_user.id, Conversation.user_two_id == current_user.id)
    ).order_by(Conversation.last_message_at.desc()).all()

    convo_data = []
    for c in convos:
        other = c.other_user(current_user.id)
        convo_data.append({
            "conversation": c,
            "other_user": other,
            "last_message": c.last_message(),
            "unread": c.unread_count_for(current_user.id),
        })

    return render_template("messages/conversations.html", convo_data=convo_data)


@messages_bp.route("/messages/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    if other_user.id == current_user.id:
        flash("You can't message yourself.", "error")
        return redirect(url_for("messages.conversations"))

    convo = get_or_create_conversation(current_user.id, other_user.id)

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            msg = Message(conversation_id=convo.id, sender_id=current_user.id, body=body)
            db.session.add(msg)
            from datetime import datetime, timezone
            convo.last_message_at = datetime.now(timezone.utc)
            notify(
                other_user.id, "new_message",
                f"New message from {current_user.name}",
                body[:120],
                url_for("messages.chat", user_id=current_user.id),
            )
            db.session.commit()
        return redirect(url_for("messages.chat", user_id=user_id))

    # mark messages as read
    unread = convo.messages.filter(Message.sender_id != current_user.id, Message.is_read.is_(False)).all()
    for m in unread:
        m.is_read = True
    if unread:
        db.session.commit()

    all_messages = convo.messages.order_by(Message.created_at.asc()).all()

    return render_template(
        "messages/chat.html", other_user=other_user, messages=all_messages, conversation=convo
    )
