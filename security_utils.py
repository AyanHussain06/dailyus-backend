import os
import uuid
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app
from functools import wraps
from flask_jwt_extended import get_jwt_identity
from models import User


def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="photo-access")


def generate_photo_token(photo_id: str, requester_id: str) -> str:
    """Create a short-lived signed token proving requester_id may view photo_id
    at the moment of issue. Verified again (with a fresh DB check) on access."""
    s = get_serializer()
    return s.dumps({"photo_id": photo_id, "user_id": requester_id})


def verify_photo_token(token: str):
    s = get_serializer()
    try:
        data = s.loads(token, max_age=current_app.config["SIGNED_URL_EXPIRY"])
        return data, None
    except SignatureExpired:
        return None, "expired"
    except BadSignature:
        return None, "invalid"


def safe_random_filename(original_filename: str) -> str:
    """Never trust the client's filename — generate our own on the server."""
    ext = ""
    if "." in original_filename:
        ext = original_filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


def current_user():
    """Helper: load the User row for the current JWT identity."""
    uid = get_jwt_identity()
    if not uid:
        return None
    return User.query.get(uid)


def require_couple(f):
    """Decorator: blocks any request from a user who isn't paired yet."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return {"error": "User not found"}, 404
        if not user.couple_id:
            return {"error": "You need to pair with a partner first"}, 403
        return f(user, *args, **kwargs)

    return wrapper


def photo_belongs_to_couple(photo, couple_id: str) -> bool:
    """The core access-control check: does this photo belong to this couple?
    Every photo read/delete MUST go through this before touching the file."""
    return photo is not None and photo.couple_id == couple_id
