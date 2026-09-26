import uuid
import secrets
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def gen_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    couple_id = db.Column(db.String(36), db.ForeignKey("couples.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_public_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Couple(db.Model):
    __tablename__ = "couples"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    invite_code = db.Column(db.String(12), unique=True, nullable=False)
    invite_code_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    streak_count = db.Column(db.Integer, default=0)
    last_streak_date = db.Column(db.Date, nullable=True)

    members = db.relationship("User", backref="couple", lazy=True)

    @staticmethod
    def generate_invite_code():
        # short, human-shareable, unambiguous characters only
        alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
        return "".join(secrets.choice(alphabet) for _ in range(6))


class Photo(db.Model):
    __tablename__ = "photos"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    couple_id = db.Column(db.String(36), db.ForeignKey("couples.id"), nullable=False, index=True)
    uploader_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # stored on disk, never exposed raw
    caption = db.Column(db.String(280), nullable=True)
    day = db.Column(db.Date, nullable=False, default=date.today, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship("User")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    couple_id = db.Column(db.String(36), db.ForeignKey("couples.id"), nullable=False, index=True)
    sender_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    sender = db.relationship("User")
