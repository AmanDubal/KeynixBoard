"""Background process: listens to every keystroke on the system and plays
the matching sound from the active theme. Runs until it receives a stop
signal (sent by `keyboard sound <name> deactivate`)."""
import argparse
import os
import signal
import sys
import time

from pynput import keyboard

from . import player
from . import state as state_mod


def classify(key) -> str:
    try:
        if key == keyboard.Key.space:
            return "space"
        if key == keyboard.Key.enter:
            return "enter"
        if key == keyboard.Key.backspace:
            return "backspace"
        if key == keyboard.Key.tab:
            return "tab"
    except Exception:
        pass
    return "generic"


def main():
    ap = argparse.ArgumentParser(prog="keyboard-sound-daemon")
    ap.add_argument("--theme-dir", required=True)
    ap.add_argument("--display-name", required=True)
    ap.add_argument("--enter-file", default=None, help="optional override wav for the Enter key")
    ap.add_argument("--volume", type=float, default=1.0)
    args = ap.parse_args()

    theme = player.load_from_dir(args.display_name, args.theme_dir)

    if args.enter_file:
        clip, sr = player.load_single_file_as_clip(args.enter_file)
        theme.set_enter_override(clip)

    engine = player.AudioEngine(samplerate=theme.sr, volume=max(0.0, min(2.0, args.volume)))

    stop_requested = {"flag": False}

    def handle_stop(signum, frame):
        stop_requested["flag"] = True

    for sig_name in ("SIGTERM", "SIGINT", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            try:
                signal.signal(sig, handle_stop)
            except (ValueError, OSError):
                pass

    def on_press(key):
        category = classify(key)
        clip = theme.clip_for(category)
        engine.trigger(clip)
        if stop_requested["flag"]:
            return False

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    state_mod.write_state(
        {
            "pid": os.getpid(),
            "theme": args.display_name,
            "theme_dir": args.theme_dir,
            "enter_file": args.enter_file,
            "volume": args.volume,
            "started_at": time.time(),
        }
    )

    try:
        while listener.is_alive() and not stop_requested["flag"]:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            listener.stop()
        except Exception:
            pass
        engine.close()
        state_mod.clear_state()


if __name__ == "__main__":
    sys.exit(main())
