import os
import time
import requests
from pathlib import Path

API_BASE = os.environ.get('API_BASE', 'http://localhost:5702/api')
TEST_DIR = os.environ.get('TEST_VOICES_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'test-voices'))


def upload_file(path):
    url = f"{API_BASE}/uploads"
    with open(path, 'rb') as f:
        files = {'file': (os.path.basename(path), f)}
        resp = requests.post(url, files=files)
    resp.raise_for_status()
    return resp.json()['id']


def request_transcription(upload_id):
    url = f"{API_BASE}/transcriptions"
    data = {'upload_id': upload_id}
    start = time.time()
    resp = requests.post(url, json=data)
    elapsed = time.time() - start
    resp.raise_for_status()
    return resp.json(), elapsed


def summarize_segments(segments):
    # segments: [{start,end,text,speaker?}]
    by_speaker = {}
    speaker_texts = {}
    total_dur = 0.0
    for seg in (segments or []):
        speaker = seg.get('speaker') or seg.get('speaker_id') or 'unknown'
        text = seg.get('text', '').strip()
        dur = (seg.get('end') or 0) - (seg.get('start') or 0)
        total_dur += max(0.0, dur)
        by_speaker.setdefault(speaker, 0.0)
        by_speaker[speaker] += max(0.0, dur)
        speaker_texts.setdefault(speaker, [])
        if text:
            speaker_texts[speaker].append(text)
    return total_dur, by_speaker, speaker_texts


def main():
    p = Path(TEST_DIR)
    if not p.exists():
        print('Test directory not found:', TEST_DIR)
        return
    wavs = sorted([x for x in p.iterdir() if x.is_file()])
    if not wavs:
        print('No files found in', TEST_DIR)
        return
    print('Found', len(wavs), 'files. Testing against', API_BASE)
    for f in wavs:
        print('\nProcessing', f.name)
        try:
            upload_id = upload_file(f)
            print(' Uploaded id:', upload_id)
        except Exception as e:
            print(' Upload failed:', e)
            continue
        try:
            result, elapsed = request_transcription(upload_id)
            text = result.get('text')
            segments = result.get('segments')
            duration, by_speaker, speaker_texts = summarize_segments(segments)
            print(f' Transcription status: {result.get("status")}, elapsed: {elapsed:.2f}s, audio_duration(seg sum): {duration:.2f}s')
            print(' Speakers and their text:')
            for spk in sorted(by_speaker.keys()):
                sec = by_speaker[spk]
                texts = speaker_texts.get(spk, [])
                combined_text = ' '.join(texts)
                # print(f'  - {spk} ({sec:.2f}s): {combined_text[:150]}{"..." if len(combined_text) > 150 else ""}')
                print(f'  - {spk} ({sec:.2f}s): {combined_text}')
            print(' Full text preview:', (text or '')[:200])
        except Exception as e:
            print(' Transcription failed:', e)

if __name__ == '__main__':
    main()
