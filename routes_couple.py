from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from models import db, Couple, User
from security_utils import current_user

couple_bp = Blueprint("couple", __name__, url_prefix="/api/couple")


@couple_bp.post("/create-invite")
@jwt_required()
def create_invite():
    """Generate a one-time, expiring invite code for this user to share
    with their partner. Only usable while the user has no partner yet."""
    user = current_user()
    if not user:
        return jsonify({"error": "Not found"}), 404
    if user.couple_id:
        return jsonify({"error": "You're already paired"}), 400

    couple = Couple(
        invite_code=Couple.generate_invite_code(),
        invite_code_expires=datetime.utcnow() + timedelta(hours=24),
    )
    db.session.add(couple)
    db.session.flush()  # get couple.id before assigning

    user.couple_id = couple.id
    db.session.commit()

    return jsonify({
        "invite_code": couple.invite_code,
        "expires_at": couple.invite_code_expires.isoformat(),
    }), 201


@couple_bp.post("/join")
@jwt_required()
def join_invite():
    user = current_user()
    if not user:
        return jsonify({"error": "Not found"}), 404
    if user.couple_id:
        return jsonify({"error": "You're already paired"}), 400

    data = request.get_json(silent=True) or {}
    code = (data.get("invite_code") or "").strip().upper()
    if not code:
        return jsonify({"error": "Invite code is required"}), 400

    couple = Couple.query.filter_by(invite_code=code).first()
    if not couple:
        return jsonify({"error": "Invalid invite code"}), 404
    if couple.invite_code_expires and couple.invite_code_expires < datetime.utcnow():
        return jsonify({"error": "This invite code has expired"}), 410

    existing_members = User.query.filter_by(couple_id=couple.id).count()
    if existing_members >= 2:
        return jsonify({"error": "This pairing is already complete"}), 409

    user.couple_id = couple.id
    db.session.commit()

    return jsonify({"message": "Paired successfully!", "couple_id": couple.id}), 200


@couple_bp.get("/status")
@jwt_required()
def status():
    user = current_user()
    if not user:
        return jsonify({"error": "Not found"}), 404
    if not user.couple_id:
        return jsonify({"paired": False}), 200

    partner = User.query.filter(
        User.couple_id == user.couple_id, User.id != user.id
    ).first()

    return jsonify({
        "paired": True,
        "couple_id": user.couple_id,
        "partner": partner.to_public_dict() if partner else None,
        "streak_count": user.couple.streak_count if user.couple else 0,
    }), 200


@couple_bp.post("/unpair")
@jwt_required()
def unpair():
    """Both partners keep their own account; the pairing (and access to
    shared photos/messages) is severed. Does not delete the other user."""
    user = current_user()
    if not user or not user.couple_id:
        return jsonify({"error": "You're not currently paired"}), 400

    couple_id = user.couple_id
    User.query.filter_by(couple_id=couple_id).update({"couple_id": None})
    db.session.commit()
    return jsonify({"message": "Unpaired. Shared content is no longer accessible to either of you."}), 200
