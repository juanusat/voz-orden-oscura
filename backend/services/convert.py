import os
import subprocess
import shutil
from pathlib import Path
from backend.config import Config


def _parse_dotenv(dotenv_path: Path):
    data = {}
    if not dotenv_path.exists():
        return data
    for line in dotenv_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        data[k] = v
    return data


def _get_ffmpeg_executable_from_envfile():
    # locate backend/.env (two levels up from this file: services -> backend)
    base = Path(__file__).resolve().parents[1]
    dotenv = base / '.env'
    env = _parse_dotenv(dotenv)
    candidates = []
    if 'FFMPEG_BIN' in env and env['FFMPEG_BIN']:
        candidates.append(env['FFMPEG_BIN'])
    if 'FFMPEG_PATH' in env and env['FFMPEG_PATH']:
        p = env['FFMPEG_PATH']
        p = os.path.expandvars(p)
        # normalize separators to OS style
        p = p.replace('/', os.sep).replace('\\', os.sep)
        exe = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
        if os.path.isdir(p):
            candidates.append(os.path.join(p, exe))
        else:
            candidates.append(p)
    for c in candidates:
        if not c:
            continue
        c = str(c)
        # if absolute path and exists, return it
        if os.path.isabs(c) and os.path.exists(c):
            return c
        # try resolving via which
        found = shutil.which(c)
        if found:
            return found
    # fallback: try finding ffmpeg in PATH
    found = shutil.which('ffmpeg')
    if found:
        return found
    raise RuntimeError('ffmpeg executable not found. Please set FFMPEG_PATH or FFMPEG_BIN in backend/.env')


def ensure_audio(input_path, output_dir, filename=None):
    input_path = str(input_path)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_name = filename or (Path(input_path).stem + ".wav")
    output_path = Path(output_dir) / out_name
    # If output would be the same file as input, choose a different output name
    try:
        in_resolved = Path(input_path).resolve()
        out_resolved = output_path.resolve()
    except Exception:
        in_resolved = Path(input_path).absolute()
        out_resolved = output_path.absolute()
    if in_resolved == out_resolved:
        out_name = Path(input_path).stem + "_conv.wav"
        output_path = Path(output_dir) / out_name

    ffmpeg = _get_ffmpeg_executable_from_envfile()
    cmd = [ffmpeg, "-y", "-i", input_path, "-vn", "-acodec", "pcm_s16le", "-ar", str(Config.DEFAULT_SAMPLE_RATE), "-ac", "1", str(output_path)]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode('utf-8', errors='replace') if getattr(e, 'stderr', None) else ''
        raise RuntimeError(f"ffmpeg failed (cmd: {cmd}): {stderr}")
    return str(output_path)
