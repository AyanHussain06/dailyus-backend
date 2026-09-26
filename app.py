import os
from flask import Flask, render_template
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from config import Config
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["COLLAGE_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

    db.init_app(app)
    JWTManager(app)
    CORS(app)  # fine for local dev; restrict origins in real deployment

    from routes_auth import auth_bp
    from routes_couple import couple_bp
    from routes_photos import photos_bp
    from routes_messages import messages_bp
    from routes_collage import collage_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(couple_bp)
    app.register_blueprint(photos_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(collage_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
