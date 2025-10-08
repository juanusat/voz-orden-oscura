from flask import Blueprint, request, current_app, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import os
from backend import db
from backend.models import Upload

uploads_bp = Blueprint("uploads", __name__)

@uploads_bp.route("", methods=["POST"])
def create_upload():
    if request.content_type and request.content_type.startswith("application/octet-stream"):
        filename = request.headers.get("X-Filename") or request.args.get("filename") or "upload.bin"
        folder = current_app.config["UPLOAD_FOLDER"]
        Path(folder).mkdir(parents=True, exist_ok=True)
        path = Path(folder) / filename
        with open(path, "wb") as f:
            f.write(request.get_data())
        content_type = request.content_type
        size = path.stat().st_size
    else:
        file = request.files.get("file")
        if not file:
            return jsonify({"error":"missing file"}), 400
        filename = secure_filename(file.filename or "upload")
        folder = current_app.config["UPLOAD_FOLDER"]
        Path(folder).mkdir(parents=True, exist_ok=True)
        path = Path(folder) / filename
        file.save(str(path))
        content_type = file.mimetype
        size = path.stat().st_size
    upload = Upload(filename=str(filename), content_type=content_type, size_bytes=size, stored_at=str(path), is_video=str(filename).lower().endswith((".mp4",".mkv",".mov",".webm")))
    db.session.add(upload)
    db.session.commit()
    return jsonify({"id":upload.id,"filename":upload.filename,"content_type":upload.content_type,"size":upload.size_bytes,"stored_at":upload.stored_at})


@uploads_bp.route("/download/<path:filename>", methods=["GET"])
def download_upload(filename):
    folder = current_app.config.get("UPLOAD_FOLDER")
    if not folder:
        return jsonify({"error": "upload folder not configured"}), 500
    # Ensure file exists inside upload folder
    safe_name = Path(filename).name
    file_path = Path(folder) / safe_name
    if not file_path.exists():
        return jsonify({"error": "not found"}), 404
    return send_from_directory(folder, safe_name, as_attachment=True)
