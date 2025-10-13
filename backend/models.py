import uuid
from sqlalchemy import Column, JSON, Text, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend import db

class Upload(db.Model):
    __tablename__ = "uploads"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(Text, nullable=False)
    content_type = Column(Text, nullable=False)
    size_bytes = Column(db.BigInteger, nullable=False, default=0)
    stored_at = Column(Text, nullable=False)
    original_path = Column(Text)
    is_video = Column(Boolean, nullable=False, default=False)
    metadata_json = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Transcription(db.Model):
    __tablename__ = "transcriptions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = Column(String, ForeignKey("uploads.id"))
    filename = Column(Text)
    content_type = Column(Text)
    audio_path = Column(Text)
    duration_seconds = Column(Float)
    language = Column(String(8))
    text = Column(Text)
    segments = Column(JSON)
    speakers = Column(JSON)
    speaker_segments = Column(JSON)
    status = Column(String(32), nullable=False, default="queued")
    error = Column(Text)
    transcriber = Column(Text)
    word_doc_path = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
