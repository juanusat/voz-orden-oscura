from flask import Blueprint, jsonify, request, current_app, send_from_directory
from backend import db
from backend.models import Transcription, Upload
from backend.services.convert import ensure_audio
from backend.services.transcribe import transcribe_audio
from backend.services.docx_generator import generate_docx
from pathlib import Path

transcriptions_bp = Blueprint("transcriptions", __name__)

@transcriptions_bp.route("", methods=["GET"])
def list_transcriptions():
    status = request.args.get("status")
    q = Transcription.query
    if status:
        q = q.filter_by(status=status)
    items = q.order_by(Transcription.created_at.desc()).limit(int(request.args.get("limit",10))).offset(int(request.args.get("offset",0))).all()
    results = []
    for t in items:
        results.append({"id":t.id,"filename":t.filename,"status":t.status,"duration_seconds":t.duration_seconds,"created_at":t.created_at.isoformat() if t.created_at else None})
    return jsonify(results)

@transcriptions_bp.route("/<string:tid>", methods=["GET"])
def get_transcription(tid):
    t = Transcription.query.get(tid)
    if not t:
        return jsonify({"error":"not found"}), 404
    return jsonify({"id":t.id,"filename":t.filename,"status":t.status,"text":t.text,"duration_seconds":t.duration_seconds,"segments":t.segments,"speakers":t.speakers,"created_at":t.created_at.isoformat() if t.created_at else None})

@transcriptions_bp.route("", methods=["POST"])
def create_transcription_sync():
    data = request.get_json() or {}
    upload_id = data.get("upload_id") or request.form.get("upload_id")
    if not upload_id:
        return jsonify({"error":"upload_id required"}),400
    upload = Upload.query.get(upload_id)
    if not upload:
        return jsonify({"error":"upload not found"}),404
    audio_path = ensure_audio(upload.stored_at, current_app.config["UPLOAD_FOLDER"])
    t = Transcription(upload_id=upload.id, filename=upload.filename, content_type=upload.content_type, audio_path=audio_path, status="processing")
    db.session.add(t)
    db.session.commit()
    try:
        res = transcribe_audio(audio_path)
        t.text = res.get("text")
        t.segments = res.get("segments")
        t.duration_seconds = res.get("duration")
        t.status = "completed"
    except Exception as e:
        t.status = "failed"
        t.error = str(e)
    db.session.commit()
    return jsonify({"id":t.id,"status":t.status,"text":t.text,"segments":t.segments})

@transcriptions_bp.route("/async", methods=["POST"])
def create_transcription_async():
    data = request.get_json() or {}
    upload_id = data.get("upload_id")
    if not upload_id:
        return jsonify({"error":"upload_id required"}),400
    upload = Upload.query.get(upload_id)
    if not upload:
        return jsonify({"error":"upload not found"}),404
    t = Transcription(upload_id=upload.id, filename=upload.filename, content_type=upload.content_type, status="queued")
    db.session.add(t)
    db.session.commit()
    return jsonify({"task_id":t.id,"status":"queued"}),202

@transcriptions_bp.route("/<string:tid>/docx", methods=["POST"])
def generate_docx_endpoint(tid):
    t = Transcription.query.get(tid)
    if not t:
        return jsonify({"error":"not found"}),404
    if t.word_doc_path:
        return jsonify({"docx_url":t.word_doc_path}),200
    folder = current_app.config["DOCX_STORAGE_PATH"]
    Path(folder).mkdir(parents=True, exist_ok=True)
    outpath = str(Path(folder) / (t.id + ".docx"))
    generate_docx(t, outpath, options=request.get_json() or {})
    t.word_doc_path = outpath
    db.session.commit()
    return jsonify({"docx_url":outpath}),201

@transcriptions_bp.route("/download/<path:filename>", methods=["GET"])
def download_docx(filename):
    folder = current_app.config["DOCX_STORAGE_PATH"]
    return send_from_directory(folder, filename, as_attachment=True)
