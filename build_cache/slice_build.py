"""
Build script: converts raw downloaded Mechvibes sound packs into the
simplified per-theme WAV asset layout used by keyboard_sound.

Run once (already run during project creation). Output goes to
../keyboard_sound/sounds/<theme>/*.wav
"""
import json
import os
import soundfile as sf
import numpy as np
from scipy.signal import butter, sosfiltfilt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "keyboard_sound", "sounds"))

# evdev-style key codes used by Mechvibes "single" sprite packs
EVDEV = {
    "esc": 1, "tab": 15, "backspace": 14, "enter": 28, "space": 57,
    "letters": [16, 17, 18, 19, 20, 30, 31, 32, 33, 44, 45, 46, 47, 48, 49, 21, 22, 23],
}

TARGET_SR = 44100


def write_wav(path, data, sr):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if data.ndim > 1:
        data = data.mean(axis=1)
    sf.write(path, data.astype(np.float32), sr, subtype="PCM_16")


def normalize(data, peak=0.9):
    m = np.max(np.abs(data)) if len(data) else 0
    if m > 0:
        data = data / m * peak
    return data


def slice_sprite_pack(pack_dir, out_theme_dir):
    cfg = json.load(open(os.path.join(pack_dir, "config.json")))
    defines = cfg["defines"]
    audio, sr = sf.read(os.path.join(pack_dir, "sound.ogg"), always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    def slice_for(code_key):
        entry = defines.get(str(code_key))
        if not entry:
            return None
        start_ms, dur_ms = entry[0], entry[1]
        start = int(sr * start_ms / 1000)
        end = int(sr * (start_ms + dur_ms) / 1000)
        return audio[start:end]

    # generic letters -> pool of variations
    idx = 0
    for code in EVDEV["letters"]:
        clip = slice_for(code)
        if clip is not None and len(clip) > 0:
            write_wav(os.path.join(out_theme_dir, f"key_{idx:02d}.wav"), normalize(clip), sr)
            idx += 1
    for name, code in (("space", 57), ("enter", 28), ("backspace", 14), ("tab", 15)):
        clip = slice_for(code)
        if clip is not None and len(clip) > 0:
            write_wav(os.path.join(out_theme_dir, f"{name}.wav"), normalize(clip), sr)
    return idx


def collect_multi_pack(pack_dir, out_theme_dir, generic_files, special_map, subdir=""):
    base = os.path.join(pack_dir, subdir)
    idx = 0
    for fname in generic_files:
        p = os.path.join(base, fname)
        if not os.path.exists(p):
            continue
        data, sr = sf.read(p, always_2d=False)
        write_wav(os.path.join(out_theme_dir, f"key_{idx:02d}.wav"), normalize(data), sr)
        idx += 1
    for name, fname in special_map.items():
        p = os.path.join(base, fname)
        if not os.path.exists(p):
            continue
        data, sr = sf.read(p, always_2d=False)
        write_wav(os.path.join(out_theme_dir, f"{name}.wav"), normalize(data), sr)
    return idx


def make_silent_from(pack_dir, out_theme_dir):
    """Derive a heavily muffled 'silent switch' pack from a real recording."""
    cfg = json.load(open(os.path.join(pack_dir, "config.json")))
    defines = cfg["defines"]
    audio, sr = sf.read(os.path.join(pack_dir, "sound.ogg"), always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    sos = butter(4, 900, btype="low", fs=sr, output="sos")

    def process(clip):
        clip = sosfiltfilt(sos, clip)
        clip = normalize(clip, peak=0.35)  # much quieter -> dampened pad feel
        return clip

    idx = 0
    for code in EVDEV["letters"]:
        entry = defines.get(str(code))
        if not entry:
            continue
        start = int(sr * entry[0] / 1000)
        end = int(sr * (entry[0] + entry[1]) / 1000)
        clip = audio[start:end]
        if len(clip):
            write_wav(os.path.join(out_theme_dir, f"key_{idx:02d}.wav"), process(clip), sr)
            idx += 1
    for name, code in (("space", 57), ("enter", 28), ("backspace", 14), ("tab", 15)):
        entry = defines.get(str(code))
        if entry:
            start = int(sr * entry[0] / 1000)
            end = int(sr * (entry[0] + entry[1]) / 1000)
            clip = audio[start:end]
            if len(clip):
                write_wav(os.path.join(out_theme_dir, f"{name}.wav"), process(clip), sr)
    return idx


def main():
    os.makedirs(OUT, exist_ok=True)

    n = slice_sprite_pack(os.path.join(HERE, "cherrymx-blue-pbt"), os.path.join(OUT, "clicky"))
    print("clicky:", n)

    n = slice_sprite_pack(os.path.join(HERE, "cherrymx-red-abs"), os.path.join(OUT, "clacky"))
    print("clacky:", n)

    n = slice_sprite_pack(os.path.join(HERE, "cherrymx-brown-pbt"), os.path.join(OUT, "mechanical"))
    print("mechanical:", n)

    n = collect_multi_pack(
        os.path.join(HERE, "nk-cream"), os.path.join(OUT, "creamy"),
        generic_files=[f"{c}.wav" for c in "abcdefghijklmnopqrstuvwxyz"],
        special_map={"space": "space.wav", "enter": "enter.wav", "backspace": "backspace.wav", "tab": "tab.wav"},
    )
    print("creamy:", n)

    n = collect_multi_pack(
        os.path.join(HERE, "holy-pandas"), os.path.join(OUT, "thocky"),
        generic_files=[f"GENERIC_R{i}.mp3" for i in range(5)],
        special_map={"space": "SPACE.mp3", "enter": "ENTER.mp3", "backspace": "BACKSPACE.mp3"},
    )
    print("thocky:", n)

    n = collect_multi_pack(
        os.path.join(HERE, "turquoise"), os.path.join(OUT, "marbly"),
        generic_files=[f"GENERIC_R{i}.mp3" for i in range(5)],
        special_map={"space": "SPACE.mp3", "enter": "ENTER.mp3", "backspace": "BACKSPACE.mp3"},
        subdir="press",
    )
    print("marbly:", n)

    n = make_silent_from(os.path.join(HERE, "topre-purple-hybrid-pbt"), os.path.join(OUT, "silent"))
    print("silent:", n)


if __name__ == "__main__":
    main()
