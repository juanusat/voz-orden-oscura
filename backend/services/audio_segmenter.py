import os
import subprocess
from pathlib import Path
from flask import current_app

def get_ffmpeg_path():
    ffmpeg_path = current_app.config.get('FFMPEG_PATH')
    if ffmpeg_path:
        return os.path.join(ffmpeg_path, 'ffmpeg.exe')
    return 'ffmpeg'

def segment_audio_by_speakers(audio_path, speaker_segments, output_dir):
    segments_info = []
    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    ffmpeg_cmd = get_ffmpeg_path()
    
    for i, segment in enumerate(speaker_segments):
        speaker_id = segment.get('speaker_id', f'speaker_{i+1}')
        start_time = segment.get('start_time', 0)
        end_time = segment.get('end_time')
        
        if end_time is None:
            if i + 1 < len(speaker_segments):
                end_time = speaker_segments[i + 1].get('start_time', start_time + 30)
            else:
                end_time = start_time + 30
        
        duration = end_time - start_time
        if duration <= 0.1:
            continue
            
        output_filename = f"{speaker_id}_segment_{i+1}_{start_time:.1f}s-{end_time:.1f}s.wav"
        output_path = output_dir / output_filename
        
        try:
            cmd = [
                ffmpeg_cmd, '-y',
                '-i', str(audio_path),
                '-ss', str(start_time),
                '-t', str(duration),
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-loglevel', 'error',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if output_path.exists() and output_path.stat().st_size > 1000:
                segments_info.append({
                    'speaker_id': speaker_id,
                    'segment_index': i + 1,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'audio_path': str(output_path),
                    'original_segment': segment
                })
            else:
                print(f"Segment too small or empty for {speaker_id}: {duration}s")
            
        except subprocess.CalledProcessError as e:
            print(f"Error segmenting audio for speaker {speaker_id}: {e.stderr}")
            continue
        except FileNotFoundError:
            print(f"FFmpeg not found at {ffmpeg_cmd}. Please check FFMPEG_PATH configuration.")
            break
    
    return segments_info

def cleanup_segments(segments_info):
    for segment in segments_info:
        try:
            os.remove(segment['audio_path'])
        except (OSError, KeyError):
            pass