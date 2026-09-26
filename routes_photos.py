import os
from datetime import date, datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory, abort
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from PIL import Image

from models import db, Photo, User
from security_utils import (
    current_user, require_couple, allowed_file, safe_random_filename,
    generate_photo_token, verify_photo_token, photo_belongs_to_couple,
)

photos_bp = Blueprint("photos", __name__, url_prefix="/api/photos")


@photos_bp.post("/upload")
@jwt_required()
@require_couple
def upload_photo(user):
    if "photo" not in request.files:
        return jsonify({"error": "No photo file provided"}), 400

    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    today = date.today()
    # One photo per person per day for the daily-check-in mechanic
    existing = Photo.query.filter_by(
        couple_id=user.couple_id, uploader_id=user.id, day=today
    ).first()
    if existing:
        return jsonify({"error": "You've already uploaded today's photo"}), 409

    filename = safe_random_filename(secure_filename(file.filename))
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    # Re-encode via Pillow (strips EXIF/GPS metadata, validates it's a real image)
    try:
        img = Image.open(file.stream)
        img.verify()
        file.stream.seek(0)
        img = Image.open(file.stream).convert("RGB")
        img.thumbnail((1600, 1600))
        img.save(save_path, format="JPEG", quality=85)
    except Exception:
        return jsonify({"error": "Invalid or corrupted image file"}), 400

    caption = (request.form.get("caption") or "").strip()[:280]

    photo = Photo(
        couple_id=user.couple_id,
        uploader_id=user.id,
        filename=filename,
        caption=caption,
        day=today,
    )
    db.session.add(photo)
    db.session.commit()

    return jsonify({"message": "Uploaded!", "photo_id": photo.id, "day": today.isoformat()}), 201


@photos_bp.get("/timeline")
@jwt_required()
@require_couple
def timeline(user):
    """List metadata for the couple's photos. Each entry gets a fresh
    short-lived access token instead of a raw file path."""
    photos = (
        Photo.query.filter_by(couple_id=user.couple_id)
        .order_by(Photo.day.desc(), Photo.created_at.desc())
        .all()
    )

    result = []
    for p in photos:
        result.append({
            "id": p.id,
            "day": p.day.isoformat(),
            "caption": p.caption,
            "uploader_name": p.uploader.name,
            "uploader_id": p.uploader_id,
            "is_mine": p.uploader_id == user.id,
            "access_token": generate_photo_token(p.id, user.id),
        })
    return jsonify({"photos": result}), 200


@photos_bp.get("/view/<photo_id>")
def view_photo(photo_id):
    """Serves the actual image bytes. Requires a valid, unexpired, signed
    token whose photo_id matches AND whose user is still in that couple —
    this double-checks against the DB rather than trusting the token alone."""
    token = request.args.get("token", "")
    data, err = verify_photo_token(token)
    if err == "expired":
        return jsonify({"error": "Link expired, refresh the page"}), 410
    if err or not data or data.get("photo_id") != photo_id:
        abort(403)

    photo = Photo.query.get(photo_id)
    requester = User.query.get(data["user_id"])
    if not requester or not requester.couple_id:
        abort(403)
    if not photo_belongs_to_couple(photo, requester.couple_id):
        abort(403)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], photo.filename, max_age=0
    )


@photos_bp.delete("/<photo_id>")
@jwt_required()
@require_couple
def delete_photo(user, photo_id):
    photo = Photo.query.get(photo_id)
    if not photo_belongs_to_couple(photo, user.couple_id):
        # Same 404 whether it doesn't exist or belongs to someone else —
        # never confirm existence of another couple's data
        return jsonify({"error": "Photo not found"}), 404
    if photo.uploader_id != user.id:
        return jsonify({"error": "You can only delete your own photos"}), 403

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], photo.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(photo)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200
