from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# try to import Flask-CORS; if not available we'll still allow setup but warn at runtime
try:
    from flask_cors import CORS
except Exception:
    CORS = None

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, static_url_path="/downloads")
    app.config.from_object("backend.config.Config")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["DOCX_STORAGE_PATH"], exist_ok=True)

    # enable CORS if flask_cors is installed; allow all origins for dev
    if CORS is not None:
        CORS(app)
    else:
        # Warn to stdout; not raising so the app can still run in environments
        print("Warning: Flask-CORS not installed. If you run frontend from a different origin, requests may be blocked by the browser.")

    db.init_app(app)
    with app.app_context():
        from backend import models
        db.create_all()
        from backend.blueprints.uploads_api import uploads_bp
        from backend.blueprints.transcriptions_api import transcriptions_bp
        app.register_blueprint(uploads_bp, url_prefix="/api/uploads")
        app.register_blueprint(transcriptions_bp, url_prefix="/api/transcriptions")
    return app
