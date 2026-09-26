import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "dailyus.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    COLLAGE_FOLDER = os.path.join(BASE_DIR, "collages")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # How long a signed photo-access token stays valid (seconds)
    SIGNED_URL_EXPIRY = 300  # 5 minutes
