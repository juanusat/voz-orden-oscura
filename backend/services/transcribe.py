try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None


def transcribe_audio(path, model_name="small", language=None, device="cpu"):
    if WhisperModel is None:
        raise RuntimeError("faster-whisper not available")
    model = WhisperModel(model_name, device=device)
    segments, info = model.transcribe(path, language=language)
    result_segments = []
    full_text = []
    for seg in segments:
        result_segments.append({"start": seg.start, "end": seg.end, "text": seg.text})
        full_text.append(seg.text)
    duration = None
    try:
        duration = float(info.duration)
    except Exception:
        pass
    return {"text": " ".join(full_text), "segments": result_segments, "duration": duration}
