"""
Builds 4 SEPARATE gun-sound themes, each with:
  - ONE consistent shot sound used for every regular key (key_00.wav)
  - a dedicated RELOAD sound mapped to the Backspace key (backspace.wav)

100% procedurally synthesized (noise + envelopes + filters) -- not real
firearm recordings -- for fun, with zero licensing/safety concerns.

Output: ../keyboard_sound/sounds/gun_pistol/, gun_shotgun/, gun_sniper/, gun_rifle/
"""
import os
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

HERE = os.path.dirname(os.path.abspath(__file__))
SOUNDS_ROOT = os.path.abspath(os.path.join(HERE, "..", "keyboard_sound", "sounds"))
SR = 44100
rng = np.random.default_rng(7)


def env_exp(n, decay):
    t = np.arange(n) / SR
    return np.exp(-decay * t)


def noise(n):
    return rng.standard_normal(n)


def bandpass(x, lo, hi, order=4):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfiltfilt(sos, x)


def lowpass(x, cut, order=4):
    sos = butter(order, cut, btype="low", fs=SR, output="sos")
    return sosfiltfilt(sos, x)


def norm(x, peak=0.9):
    m = np.max(np.abs(x))
    return x / m * peak if m > 0 else x


def write(theme, name, x):
    d = os.path.join(SOUNDS_ROOT, theme)
    os.makedirs(d, exist_ok=True)
    sf.write(os.path.join(d, name), norm(x).astype(np.float32), SR, subtype="PCM_16")


def click_event(n, lo, hi, decay, ring_freqs=(), ring_decay=None):
    m = int(SR * n)
    click = bandpass(noise(m), lo, hi) * env_exp(m, decay)
    if ring_freqs:
        rd = ring_decay or decay * 1.3
        ring = sum(np.sin(2 * np.pi * f * np.arange(m) / SR) for f in ring_freqs)
        click = click + ring * env_exp(m, rd) * 0.18
    return click


def sequence(events, total_dur):
    """events: list of (delay_s, array). Mixes them into one buffer."""
    n = int(SR * total_dur)
    out = np.zeros(n)
    for delay, seg in events:
        s = int(SR * delay)
        e = min(n, s + len(seg))
        if s < n:
            out[s:e] += seg[: e - s]
    return out


# ---------------------------------------------------------------- PISTOL ---
def pistol_shot():
    n = int(SR * 0.18)
    crack = bandpass(noise(n), 800, 6000) * env_exp(n, 55)
    sub = np.sin(2 * np.pi * 120 * np.arange(n) / SR) * env_exp(n, 90) * 0.6
    mech = click_event(0.05, 2000, 8000, 120)
    out = crack.copy()
    out[: len(sub)] += sub
    s = int(SR * 0.02)
    out[s:s + len(mech)] += mech * 0.5
    return out


def pistol_reload():
    # quick double-click: mag release + mag slap-in
    ev1 = click_event(0.02, 1200, 7000, 140, ring_freqs=(2200, 3400, 5200))
    ev2 = click_event(0.03, 1200, 7000, 110, ring_freqs=(1800, 2600, 4200))
    return sequence([(0.0, ev1), (0.09, ev2)], 0.22)


# --------------------------------------------------------------- SHOTGUN ---
def shotgun_shot():
    n = int(SR * 0.45)
    boom = bandpass(noise(n), 60, 1200) * env_exp(n, 9)
    crack = bandpass(noise(int(SR * 0.08)), 700, 5000) * env_exp(int(SR * 0.08), 40)
    sub = np.sin(2 * np.pi * 70 * np.arange(n) / SR) * env_exp(n, 7) * 0.8
    out = boom + sub
    out[: len(crack)] += crack * 1.1
    clack_delay = int(SR * 0.22)
    clack = bandpass(noise(int(SR * 0.05)), 1500, 5000) * env_exp(int(SR * 0.05), 70)
    if clack_delay + len(clack) < n:
        out[clack_delay:clack_delay + len(clack)] += clack * 0.7
    return out


def shotgun_reload():
    # shell insert thunk + heavy pump rack (cha-CHUNK)
    thunk = click_event(0.03, 150, 1500, 70, ring_freqs=(260,))
    rack1 = click_event(0.04, 900, 4000, 90, ring_freqs=(1200, 2000))
    rack2 = click_event(0.05, 700, 3500, 70, ring_freqs=(900, 1500))
    return sequence([(0.0, thunk), (0.11, rack1), (0.24, rack2)], 0.42)


# ---------------------------------------------------------------- SNIPER ---
def sniper_shot():
    n = int(SR * 0.7)
    # very sharp supersonic crack (bright, fast)
    crack = bandpass(noise(int(SR * 0.05)), 1200, 9000) * env_exp(int(SR * 0.05), 35)
    # huge deep boom with long tail (powerful long-range cartridge)
    boom = bandpass(noise(n), 50, 900) * env_exp(n, 4.5)
    sub = np.sin(2 * np.pi * 55 * np.arange(n) / SR) * env_exp(n, 4) * 0.9
    out = boom + sub
    out[: len(crack)] += crack * 1.4
    return out


def sniper_reload():
    # slow, deliberate bolt-action: lift - pull - push - lock
    lift = click_event(0.03, 1800, 6000, 150, ring_freqs=(3000,))
    pull = click_event(0.05, 600, 3000, 60, ring_freqs=(900,))
    push = click_event(0.05, 600, 3000, 60, ring_freqs=(950,))
    lock = click_event(0.03, 2000, 7000, 160, ring_freqs=(3200, 4800))
    return sequence(
        [(0.0, lift), (0.14, pull), (0.34, push), (0.50, lock)], 0.62
    )


# ----------------------------------------------------------------- RIFLE ---
def rifle_shot():
    n = int(SR * 0.16)
    # snappier / higher-pitched than pistol (closed-bolt sharp report)
    crack = bandpass(noise(n), 1000, 8000) * env_exp(n, 75)
    sub = np.sin(2 * np.pi * 150 * np.arange(n) / SR) * env_exp(n, 110) * 0.5
    gas = click_event(0.04, 2500, 9000, 160)
    out = crack.copy()
    out[: len(sub)] += sub
    s = int(SR * 0.015)
    out[s:s + len(gas)] += gas * 0.45
    return out


def rifle_reload():
    # mag-out thud, mag-in clack, charging handle ping
    mag_out = click_event(0.04, 300, 2000, 70, ring_freqs=(400,))
    mag_in = click_event(0.03, 500, 2800, 90, ring_freqs=(700, 1100))
    bolt = click_event(0.04, 2200, 8000, 150, ring_freqs=(3400, 5200))
    return sequence([(0.0, mag_out), (0.13, mag_in), (0.27, bolt)], 0.46)


def main():
    themes = {
        "gun_pistol": (pistol_shot, pistol_reload),
        "gun_shotgun": (shotgun_shot, shotgun_reload),
        "gun_sniper": (sniper_shot, sniper_reload),
        "gun_rifle": (rifle_shot, rifle_reload),
    }
    for theme, (shot_fn, reload_fn) in themes.items():
        write(theme, "key_00.wav", shot_fn())
        write(theme, "backspace.wav", reload_fn())
        print(theme, "->", os.listdir(os.path.join(SOUNDS_ROOT, theme)))


if __name__ == "__main__":
    main()
