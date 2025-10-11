from .transcription_engine import get_transcription_engine


def transcribe_audio(path, **kwargs):
    engine = get_transcription_engine()
    return engine.transcribe(path, **kwargs)
