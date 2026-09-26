import os
import math
from datetime import date, timedelta
from flask import Blueprint, request, jsonify, current_app, send_from_directory, abort
from flask_jwt_extended import jwt_required
from PIL import Image

from models import Photo, User
from security_utils import require_couple, generate_photo_token, verify_photo_token, photo_belongs_to_couple

collage_bp = Blueprint("collage", __name__, url_prefix="/api/collage")

TILE = 400  # px per photo tile in the grid


@collage_bp.post("/generate")
@jwt_required()
@require_couple
def generate_collage(user):
    data = request.get_json(silent=True) or {}
    days_back = int(data.get("days", 7))
    days_back = max(1, min(days_back, 31))

    since = date.today() - timedelta(days=days_back)
    photos = (
        Photo.query.filter(Photo.couple_id == user.couple_id, Photo.day >= since)
        .order_by(Photo.day.asc(), Photo.created_at.asc())
        .all()
    )

    if not photos:
        return jsonify({"error": "No photos in that range yet"}), 404

    n = len(photos)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    canvas = Image.new("RGB", (cols * TILE, rows * TILE), color=(20, 20, 24))

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    for idx, photo in enumerate(photos):
        path = os.path.join(upload_dir, photo.filename)
        if not os.path.exists(path):
            continue
        img = Image.open(path).convert("RGB")
        # center-crop to square, then resize to tile size
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side)).resize((TILE, TILE))

        col = idx % cols
        row = idx // cols
        canvas.paste(img, (col * TILE, row * TILE))

    collage_filename = f"{user.couple_id}_{since.isoformat()}.jpg"
    collage_path = os.path.join(current_app.config["COLLAGE_FOLDER"], collage_filename)
    canvas.save(collage_path, format="JPEG", quality=90)

    token = generate_photo_token(collage_filename, user.id)
    return jsonify({
        "message": "Collage generated!",
        "photo_count": n,
        "collage_token": token,
        "collage_filename": collage_filename,
    }), 201


@collage_bp.get("/view/<collage_filename>")
def view_collage(collage_filename):
    token = request.args.get("token", "")
    data, err = verify_photo_token(token)
    if err or not data or data.get("photo_id") != collage_filename:
        abort(403)

    requester = User.query.get(data["user_id"])
    if not requester or not requester.couple_id:
        abort(403)
    # Collage filenames are namespaced by couple_id — verify prefix match
    if not collage_filename.startswith(requester.couple_id + "_"):
        abort(403)

    return send_from_directory(
        current_app.config["COLLAGE_FOLDER"], collage_filename, max_age=0
    )
