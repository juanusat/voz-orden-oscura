import os
import subprocess
from pathlib import Path
from backend.config import Config


def ensure_audio(input_path, output_dir, filename=None):
    input_path = str(input_path)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_name = filename or (Path(input_path).stem + ".wav")
    output_path = str(Path(output_dir) / out_name)
    ffmpeg = os.environ.get("FFMPEG_BIN", Config.FFMPEG_BIN)
    cmd = [ffmpeg, "-y", "-i", input_path, "-vn", "-acodec", "pcm_s16le", "-ar", str(Config.DEFAULT_SAMPLE_RATE), "-ac", "1", output_path]
    subprocess.check_call(cmd)
    return output_path
