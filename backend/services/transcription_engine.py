from abc import ABC, abstractmethod
from flask import current_app


class TranscriptionEngine(ABC):
    @abstractmethod
    def transcribe(self, audio_path, **kwargs):
        pass


class WhisperEngine(TranscriptionEngine):
    def __init__(self):
        try:
            from faster_whisper import WhisperModel
            self.WhisperModel = WhisperModel
        except ImportError:
            self.WhisperModel = None
    
    def transcribe(self, audio_path, **kwargs):
        if self.WhisperModel is None:
            raise RuntimeError("faster-whisper not available")
        model_name = current_app.config.get("WHISPER_MODEL", "small")
        device = current_app.config.get("WHISPER_DEVICE", "cpu")
        language = kwargs.get("language")
        
        model = self.WhisperModel(model_name, device=device)
        segments, info = model.transcribe(audio_path, language=language)
        
        result_segments = []
        full_text = []
        for seg in segments:
            result_segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "speaker": "speaker_0"
            })
            full_text.append(seg.text)
        
        duration = None
        try:
            duration = float(info.duration)
        except Exception:
            pass
        
        return {
            "text": " ".join(full_text),
            "segments": result_segments,
            "duration": duration
        }


class VoskEngine(TranscriptionEngine):
    def __init__(self):
        try:
            import vosk
            import json
            import wave
            import numpy as np
            from scipy.spatial.distance import cosine
            self.vosk = vosk
            self.json = json
            self.wave = wave
            self.np = np
            self.cosine = cosine
        except ImportError as e:
            raise RuntimeError(f"Vosk dependencies not available: {e}")
    
    def transcribe(self, audio_path, **kwargs):
        model_path = current_app.config.get("VOSK_MODEL_PATH", "vosk-model-small-es-0.42")
        speaker_model_path = current_app.config.get("VOSK_SPEAKER_MODEL_PATH", "vosk-model-spk-0.4")
        
        try:
            model = self.vosk.Model(model_path)
            spk_model = None
            try:
                spk_model = self.vosk.SpkModel(speaker_model_path)
            except Exception:
                pass
        except Exception as e:
            raise RuntimeError(f"Error loading Vosk models: {e}")
        
        try:
            wf = self.wave.open(audio_path, 'rb')
            sample_rate = wf.getframerate()
            if wf.getnchannels() != 1:
                raise RuntimeError("Audio must be mono")
            if wf.getsampwidth() != 2:
                raise RuntimeError("Audio must be 16-bit")
        except Exception as e:
            raise RuntimeError(f"Error opening audio file: {e}")
        
        rec = self.vosk.KaldiRecognizer(model, sample_rate)
        rec.SetWords(True)
        if spk_model:
            rec.SetSpkModel(spk_model)
        
        segments = []
        speakers_embeddings = []
        speaker_segments = []
        current_time = 0.0
        frame_duration = 4000 / sample_rate
        
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            
            if rec.AcceptWaveform(data):
                result = self.json.loads(rec.Result())
                if result.get('text'):
                    words = result.get('result', [])
                    if words:
                        start_time = words[0].get('start', current_time)
                        end_time = words[-1].get('end', current_time + frame_duration)
                    else:
                        start_time = current_time
                        end_time = current_time + frame_duration
                    
                    segment = {
                        "start": start_time,
                        "end": end_time,
                        "text": result.get('text'),
                        "spk": result.get('spk', []) if spk_model else []
                    }
                    segments.append(segment)
                    if spk_model and segment['spk']:
                        speakers_embeddings.append(segment['spk'])
                        speaker_segments.append(len(segments) - 1)
            
            current_time += frame_duration
        
        final_result = self.json.loads(rec.FinalResult())
        if final_result.get('text'):
            words = final_result.get('result', [])
            if words:
                start_time = words[0].get('start', current_time)
                end_time = words[-1].get('end', current_time + frame_duration)
            else:
                start_time = current_time
                end_time = current_time + frame_duration
            
            segment = {
                "start": start_time,
                "end": end_time,
                "text": final_result.get('text'),
                "spk": final_result.get('spk', []) if spk_model else []
            }
            segments.append(segment)
            if spk_model and segment['spk']:
                speakers_embeddings.append(segment['spk'])
                speaker_segments.append(len(segments) - 1)
        
        wf.close()
        
        speaker_labels = {}
        if spk_model and speakers_embeddings:
            speaker_labels = self._cluster_speakers(speakers_embeddings, speaker_segments)
        
        result_segments = []
        full_text = []
        
        for i, seg in enumerate(segments):
            speaker_id = speaker_labels.get(i, "speaker_0")
            result_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "speaker": speaker_id
            })
            full_text.append(seg["text"])
        
        duration = sum((seg["end"] - seg["start"]) for seg in result_segments) if result_segments else None
        
        return {
            "text": " ".join(full_text),
            "segments": result_segments,
            "duration": duration
        }
    
    def _cluster_speakers(self, embeddings, segment_indices, threshold=0.7):
        if not embeddings:
            return {}
        
        speaker_labels = {}
        speakers = []
        
        for i, (embedding, seg_idx) in enumerate(zip(embeddings, segment_indices)):
            if not speakers:
                speakers.append([embedding])
                speaker_labels[seg_idx] = f"speaker_{len(speakers)-1}"
                continue
            
            min_distance = float('inf')
            best_speaker = -1
            
            for j, speaker_embeddings in enumerate(speakers):
                avg_embedding = self.np.mean(speaker_embeddings, axis=0)
                distance = self.cosine(embedding, avg_embedding)
                if distance < min_distance:
                    min_distance = distance
                    best_speaker = j
            
            if min_distance < threshold:
                speakers[best_speaker].append(embedding)
                speaker_labels[seg_idx] = f"speaker_{best_speaker}"
            else:
                speakers.append([embedding])
                speaker_labels[seg_idx] = f"speaker_{len(speakers)-1}"
        
        return speaker_labels


def get_transcription_engine():
    engine_name = current_app.config.get("TRANSCRIPTION_ENGINE", "vosk").lower()
    
    if engine_name == "whisper":
        return WhisperEngine()
    elif engine_name == "vosk":
        return VoskEngine()
    else:
        raise ValueError(f"Unknown transcription engine: {engine_name}")