import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///data.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    DOCX_STORAGE_PATH = os.environ.get("DOCX_STORAGE_PATH", "generated/docs")
    FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")
    DEFAULT_SAMPLE_RATE = int(os.environ.get("DEFAULT_SAMPLE_RATE", "16000"))
    
    TRANSCRIPTION_ENGINE = os.environ.get("TRANSCRIPTION_ENGINE", "vosk")
    
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
    WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
    
    VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", "vosk-model-small-es-0.42")
    VOSK_SPEAKER_MODEL_PATH = os.environ.get("VOSK_SPEAKER_MODEL_PATH", "vosk-model-spk-0.2")
    
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
    PYANNOTE_MODEL = os.environ.get("PYANNOTE_MODEL", "pyannote/speaker-diarization-3.1")
    PYANNOTE_ACCESS_TOKEN = os.environ.get("HUGGINGFACE_API_KEY")
