"""
Downloads the "Fahh" meme sound effect audio from YouTube and trims it to
the actual sound (skipping the silent lead-in/out), producing:
  ../keyboard_sound/sounds/fahh/key_00.wav

Requires: pip install yt-dlp   (and ffmpeg on PATH, for audio extraction)
Source: https://www.youtube.com/watch?v=VP6eZu3SAak ("Fahh" - meme sound effect)
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.abspath(os.path.join(HERE, "..", "keyboard_sound", "sounds", "fahh"))
URL = "https://www.youtube.com/watch?v=VP6eZu3SAak"
RAW = os.path.join(HERE, "fahh_raw.wav")


def main():
    subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "wav", "--no-warnings", "-o", RAW.replace(".wav", ".%(ext)s"), URL],
        check=True,
    )

    data, sr = sf.read(RAW)
    if data.ndim > 1:
        data = data.mean(axis=1)

    # Trim silence (keep a small margin), based on amplitude threshold.
    thr = 0.02 * np.max(np.abs(data))
    idx = np.where(np.abs(data) > thr)[0]
    start = max(0, idx[0] - int(0.03 * sr))
    end = min(len(data), idx[-1] + int(0.05 * sr))
    clip = data[start:end].astype(np.float64)

    fade_n = int(0.01 * sr)
    clip[:fade_n] *= np.linspace(0, 1, fade_n)
    clip[-fade_n:] *= np.linspace(1, 0, fade_n)

    m = np.max(np.abs(clip))
    clip = clip / m * 0.9

    os.makedirs(OUT_DIR, exist_ok=True)
    sf.write(os.path.join(OUT_DIR, "key_00.wav"), clip.astype(np.float32), sr, subtype="PCM_16")
    os.remove(RAW)
    print("wrote", os.path.join(OUT_DIR, "key_00.wav"), "duration:", len(clip) / sr, "s")


if __name__ == "__main__":
    sys.exit(main())
