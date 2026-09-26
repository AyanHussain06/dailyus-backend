from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Message
from security_utils import require_couple

messages_bp = Blueprint("messages", __name__, url_prefix="/api/messages")


@messages_bp.get("")
@jwt_required()
@require_couple
def get_messages(user):
    # Simple pagination so a long chat history doesn't get dumped in one go
    limit = min(int(request.args.get("limit", 50)), 200)
    msgs = (
        Message.query.filter_by(couple_id=user.couple_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    msgs.reverse()
    return jsonify({
        "messages": [
            {
                "id": m.id,
                "text": m.text,
                "sender_id": m.sender_id,
                "sender_name": m.sender.name,
                "is_mine": m.sender_id == user.id,
                "created_at": m.created_at.isoformat(),
            }
            for m in msgs
        ]
    }), 200


@messages_bp.post("")
@jwt_required()
@require_couple
def send_message(user):
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Message text is required"}), 400
    if len(text) > 2000:
        return jsonify({"error": "Message too long"}), 400

    msg = Message(couple_id=user.couple_id, sender_id=user.id, text=text)
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        "id": msg.id,
        "text": msg.text,
        "sender_id": msg.sender_id,
        "created_at": msg.created_at.isoformat(),
    }), 201
