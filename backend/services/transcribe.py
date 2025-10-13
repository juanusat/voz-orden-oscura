from .transcription_engine import get_transcription_engine
from .audio_segmenter import segment_audio_by_speakers, cleanup_segments
import tempfile
import os
from pathlib import Path


def transcribe_audio(path, **kwargs):
    engine = get_transcription_engine()
    speaker_segments = kwargs.get('speaker_segments', [])
    
    if not speaker_segments:
        return engine.transcribe(path, **kwargs)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        segments_info = segment_audio_by_speakers(path, speaker_segments, temp_dir)
        
        if not segments_info:
            return engine.transcribe(path, **kwargs)
        
        speaker_transcriptions = {}
        all_segments = []
        full_text_parts = []
        
        for segment in segments_info:
            try:
                segment_result = engine.transcribe(segment['audio_path'], language='es', **kwargs)
                speaker_id = segment['speaker_id']
                
                if speaker_id not in speaker_transcriptions:
                    speaker_transcriptions[speaker_id] = {
                        'speaker_id': speaker_id,
                        'text': '',
                        'segments': []
                    }
                
                segment_text = segment_result.get('text', '').strip()
                if segment_text:
                    speaker_transcriptions[speaker_id]['text'] += f" {segment_text}".strip()
                
                if segment_result.get('segments'):
                    for seg in segment_result['segments']:
                        adjusted_seg = {
                            'start': seg.get('start', 0) + segment['start_time'],
                            'end': seg.get('end', 0) + segment['start_time'],
                            'text': seg.get('text', ''),
                            'speaker': speaker_id
                        }
                        all_segments.append(adjusted_seg)
                        speaker_transcriptions[speaker_id]['segments'].append(adjusted_seg)
                
                if segment_text:
                    full_text_parts.append({
                        'start_time': segment['start_time'],
                        'speaker_id': speaker_id,
                        'text': segment_text
                    })
                
            except Exception as e:
                print(f"Error transcribing segment for {segment['speaker_id']}: {e}")
                continue
        
        cleanup_segments(segments_info)
        
        all_segments.sort(key=lambda x: x['start'])
        full_text_parts.sort(key=lambda x: x['start_time'])
        
        full_text = '\n'.join([f"[{part['speaker_id'].replace('speaker_', 'Ponente ')}]: {part['text']}" for part in full_text_parts if part['text'].strip()])
        
        total_duration = max((seg['end'] for seg in all_segments), default=0)
        if not total_duration and segments_info:
            total_duration = max((seg['end_time'] for seg in segments_info), default=0)
        
        return {
            'text': full_text,
            'segments': all_segments,
            'speakers': list(speaker_transcriptions.values()),
            'duration': total_duration,
            'speaker_segments_processed': len(segments_info)
        }
