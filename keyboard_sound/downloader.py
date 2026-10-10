"""Fetch/convert a user-supplied custom sound (URL or local file) into a
cached mono WAV usable by the player."""
import hashlib
import os
import shutil
import urllib.request

import soundfile as sf

from . import state


def _cache_path_for(key: str) -> str:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    d = os.path.join(state.custom_sounds_dir(), h)
    os.makedirs(d, exist_ok=True)
    return d


def _download(url: str, dest_path: str):
    req = urllib.request.Request(url, headers={"User-Agent": "keyboard-sound/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as out:
        shutil.copyfileobj(resp, out)


def _ensure_wav(src_path: str, dest_wav: str):
    """Try to decode directly with soundfile; fall back to ffmpeg via pydub."""
    try:
        data, sr = sf.read(src_path, always_2d=False)
        sf.write(dest_wav, data, sr, subtype="PCM_16")
        return
    except Exception:
        pass
    try:
        from pydub import AudioSegment  # requires ffmpeg on PATH for non-wav/flac/ogg formats

        seg = AudioSegment.from_file(src_path)
        seg = seg.set_channels(1)
        seg.export(dest_wav, format="wav")
        return
    except Exception as exc:
        raise RuntimeError(
            "Could not decode that audio file. WAV/FLAC/OGG work out of the box; "
            "for MP3/M4A/etc. please install ffmpeg and the 'pydub' package. "
            f"(underlying error: {exc})"
        )


def prepare_custom_sound(source: str) -> str:
    """source: http(s) URL or local file path. Returns a directory containing
    a single 'key_00.wav' ready to be loaded as a one-sound Theme."""
    cache_dir = _cache_path_for(source)
    out_wav = os.path.join(cache_dir, "key_00.wav")
    if os.path.exists(out_wav):
        return cache_dir

    if source.lower().startswith("http://") or source.lower().startswith("https://"):
        raw_path = os.path.join(cache_dir, "raw_download")
        _download(source, raw_path)
        _ensure_wav(raw_path, out_wav)
        try:
            os.remove(raw_path)
        except OSError:
            pass
    else:
        if not os.path.exists(source):
            raise FileNotFoundError(f"No such file: {source}")
        _ensure_wav(source, out_wav)

    return cache_dir
