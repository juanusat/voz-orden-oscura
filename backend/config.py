import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///data.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    DOCX_STORAGE_PATH = os.environ.get("DOCX_STORAGE_PATH", "generated/docs")
    FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")
    DEFAULT_SAMPLE_RATE = int(os.environ.get("DEFAULT_SAMPLE_RATE", "16000"))
