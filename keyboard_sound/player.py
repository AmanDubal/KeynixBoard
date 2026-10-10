"""Low-latency overlapping sound playback + theme loading."""
import glob
import os
import random
import threading

import numpy as np
import soundfile as sf
import sounddevice as sd

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

BUILTIN_THEMES = [
    "thocky", "creamy", "clacky", "clicky", "marbly", "silent", "mechanical",
    "fahh",
    "gun_pistol", "gun_shotgun", "gun_sniper", "gun_rifle",
]

THEME_DESCRIPTIONS = {
    "thocky": "Deep, low-pitched, rounded & satisfyingly muted (Holy Pandas).",
    "creamy": "Smooth, buttery, muted with a slightly higher pitch (NK Cream).",
    "clacky": "Bright, crisp, higher-pitched hard-plastic bottom-out (Cherry MX Red + ABS).",
    "clicky": "Loud, sharp mechanical click jacket sound (Cherry MX Blue).",
    "marbly": "Resonant, glassy-marbles-colliding clack (Gateron Turquoise).",
    "silent": "Heavily dampened, near-silent muffled thock (silicone-pad style).",
    "mechanical": "Balanced, general-purpose mechanical keyboard tactile sound (Cherry MX Brown).",
    "fahh": "😂 The 'Fahh' meme sound effect plays on every single keystroke.",
    "gun_pistol": "🔫 Every key fires a pistol crack. Backspace = pistol reload.",
    "gun_shotgun": "🔫 Every key fires a shotgun blast. Backspace = pump-action reload.",
    "gun_sniper": "🔫 Every key fires a powerful sniper crack+boom. Backspace = bolt-action reload.",
    "gun_rifle": "🔫 Every key fires a sharp rifle crack. Backspace = mag-swap + bolt reload.",
}


def list_builtin_themes():
    return list(BUILTIN_THEMES)


class Theme:
    """Holds loaded numpy arrays for a sound theme/pack."""

    def __init__(self, name, directory):
        self.name = name
        self.directory = directory
        self.sr = 44100
        self.pool = []  # generic variation pool for ordinary keys
        self.special = {}  # key_category -> np.array ("space","enter","backspace","tab")
        self._load()

    def _read(self, path):
        data, sr = sf.read(path, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        if sr != self.sr and self.pool == [] and not self.special:
            self.sr = sr
        return data, sr

    def _load(self):
        key_files = sorted(glob.glob(os.path.join(self.directory, "key_*.wav")))
        if not key_files:
            # single custom sound: use any audio file in the dir for everything
            any_files = [p for p in glob.glob(os.path.join(self.directory, "*")) if os.path.isfile(p)]
            for p in any_files:
                data, sr = self._read(p)
                self.pool.append(data)
                self.sr = sr
        else:
            for p in key_files:
                data, sr = self._read(p)
                self.pool.append(data)
                self.sr = sr
        for cat in ("space", "enter", "backspace", "tab"):
            p = os.path.join(self.directory, f"{cat}.wav")
            if os.path.exists(p):
                data, sr = self._read(p)
                self.special[cat] = data

    def set_enter_override(self, clip_array):
        self.special["enter"] = clip_array

    def clip_for(self, category: str):
        if category in self.special:
            return self.special[category]
        if self.pool:
            return random.choice(self.pool)
        return None


def load_builtin(name: str) -> Theme:
    name = name.lower()
    if name not in BUILTIN_THEMES:
        raise ValueError(f"Unknown built-in theme: {name}")
    return Theme(name, os.path.join(SOUNDS_DIR, name))


def load_from_dir(name: str, directory: str) -> Theme:
    return Theme(name, directory)


def load_single_file_as_clip(path: str):
    data, sr = sf.read(path, dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data, sr


class AudioEngine:
    """Persistent output stream that mixes overlapping one-shot clips."""

    def __init__(self, samplerate=44100, volume=1.0):
        self.samplerate = samplerate
        self.volume = volume
        self._lock = threading.Lock()
        self._active = []  # list of [array, position]
        self._stream = sd.OutputStream(
            samplerate=samplerate, channels=1, dtype="float32", callback=self._callback, blocksize=256
        )
        self._stream.start()

    def _callback(self, outdata, frames, time_info, status):
        mix = np.zeros(frames, dtype=np.float32)
        with self._lock:
            still_active = []
            for arr, pos in self._active:
                end = pos + frames
                chunk = arr[pos:end]
                mix[: len(chunk)] += chunk
                if end < len(arr):
                    still_active.append([arr, end])
            self._active = still_active
        np.clip(mix, -1.0, 1.0, out=mix)
        outdata[:, 0] = mix * self.volume

    def trigger(self, clip: np.ndarray):
        if clip is None or len(clip) == 0:
            return
        with self._lock:
            self._active.append([clip.astype(np.float32), 0])

    def close(self):
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
