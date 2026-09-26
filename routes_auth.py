from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from models import db, User
from security_utils import current_user
import re

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists"}), 409

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({"token": token, "user": user.to_public_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    # Deliberately vague error to avoid leaking which part was wrong
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=user.id)
    return jsonify({"token": token, "user": user.to_public_dict()}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "Not found"}), 404
    result = user.to_public_dict()
    result["paired"] = bool(user.couple_id)
    return jsonify(result), 200
