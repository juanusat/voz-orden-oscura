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
        model_name = current_app.config.get("WHISPER_MODEL", "large-v3")
        device = current_app.config.get("WHISPER_DEVICE", "cpu")
        language = kwargs.get("language", "es")
        
        try:
            compute_type = current_app.config.get("WHISPER_COMPUTE_TYPE", "float32")
            beam_size = current_app.config.get("WHISPER_BEAM_SIZE", 5)
            best_of = current_app.config.get("WHISPER_BEST_OF", 5)
            temperature = current_app.config.get("WHISPER_TEMPERATURE", 0.0)
            
            model = self.WhisperModel(
                model_name, 
                device=device,
                compute_type=compute_type,
                cpu_threads=4 if device == "cpu" else 0
            )
            segments, info = model.transcribe(
                audio_path, 
                language=language,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=300,
                    threshold=0.5,
                    min_speech_duration_ms=250
                ),
                beam_size=beam_size,
                best_of=best_of,
                temperature=temperature,
                condition_on_previous_text=True,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                repetition_penalty=1.0,
                length_penalty=1.0
            )
            
            result_segments = []
            full_text = []
            
            for seg in segments:
                text = seg.text.strip()
                if text:
                    result_segments.append({
                        "start": round(seg.start, 2),
                        "end": round(seg.end, 2),
                        "text": text,
                        "speaker": kwargs.get("speaker", "speaker_0")
                    })
                    full_text.append(text)
            
            duration = None
            try:
                duration = float(info.duration)
            except Exception:
                if result_segments:
                    duration = max(seg["end"] for seg in result_segments)
            
            return {
                "text": " ".join(full_text),
                "segments": result_segments,
                "duration": duration
            }
            
        except Exception as e:
            raise RuntimeError(f"Error transcribing with Whisper: {e}")


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


class PyannoteWhisperEngine(TranscriptionEngine):
    def __init__(self):
        try:
            from faster_whisper import WhisperModel
            from pyannote.audio import Pipeline
            import torch
            import torchaudio
            import os
            self.WhisperModel = WhisperModel
            self.Pipeline = Pipeline
            self.torch = torch
            self.torchaudio = torchaudio
            self.os = os
        except ImportError as e:
            raise RuntimeError(f"PyannoteWhisper dependencies not available: {e}")
    
    def transcribe(self, audio_path, **kwargs):
        model_name = current_app.config.get("WHISPER_MODEL", "small")
        device = current_app.config.get("WHISPER_DEVICE", "cpu")
        language = kwargs.get("language")
        hf_token = current_app.config.get("HUGGINGFACE_API_KEY")
        pyannote_model = current_app.config.get("PYANNOTE_MODEL", "pyannote/speaker-diarization-3.1")
        
        if not hf_token:
            raise RuntimeError("HUGGINGFACE_API_KEY required for PyannoteWhisper engine")
        
        self.os.environ["HF_TOKEN"] = hf_token
        
        try:
            whisper_model = self.WhisperModel(model_name, device=device)
        except Exception as e:
            raise RuntimeError(f"Error loading Whisper model: {e}")
        
        try:
            diarization_pipeline = self.Pipeline.from_pretrained(
                pyannote_model,
                use_auth_token=hf_token
            )
            if device != "cpu":
                diarization_pipeline = diarization_pipeline.to(self.torch.device(device))
        except Exception as e:
            raise RuntimeError(f"Error loading Pyannote model: {e}")
        
        try:
            segments, info = whisper_model.transcribe(audio_path, language=language)
            whisper_segments = list(segments)
        except Exception as e:
            raise RuntimeError(f"Error transcribing with Whisper: {e}")
        
        try:
            diarization = diarization_pipeline(audio_path)
        except Exception as e:
            raise RuntimeError(f"Error with speaker diarization: {e}")
        
        speaker_segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        
        result_segments = []
        full_text = []
        
        for whisper_seg in whisper_segments:
            seg_start = whisper_seg.start
            seg_end = whisper_seg.end
            seg_text = whisper_seg.text
            
            assigned_speaker = "speaker_0"
            max_overlap = 0
            
            for spk_seg in speaker_segments:
                overlap_start = max(seg_start, spk_seg["start"])
                overlap_end = min(seg_end, spk_seg["end"])
                overlap_duration = max(0, overlap_end - overlap_start)
                
                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    assigned_speaker = spk_seg["speaker"]
            
            result_segments.append({
                "start": seg_start,
                "end": seg_end,
                "text": seg_text,
                "speaker": assigned_speaker
            })
            full_text.append(seg_text)
        
        duration = None
        try:
            duration = float(info.duration)
        except Exception:
            if result_segments:
                duration = max(seg["end"] for seg in result_segments)
        
        return {
            "text": " ".join(full_text),
            "segments": result_segments,
            "duration": duration
        }


def get_transcription_engine():
    engine_name = current_app.config.get("TRANSCRIPTION_ENGINE", "vosk").lower()
    
    if engine_name == "whisper":
        return WhisperEngine()
    elif engine_name == "vosk":
        return VoskEngine()
    elif engine_name == "pyannote-whisper":
        return PyannoteWhisperEngine()
    else:
        raise ValueError(f"Unknown transcription engine: {engine_name}")