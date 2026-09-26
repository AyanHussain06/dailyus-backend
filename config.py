import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_db_url(url):
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    _database_url = _normalize_db_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_DATABASE_URI = _database_url or (
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "dailyus.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    COLLAGE_FOLDER = os.path.join(BASE_DIR, "collages")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    SIGNED_URL_EXPIRY = 300  # 5 minutes
