"""
Command-line interface.

Usage:
    keyboard sound list
    keyboard sound <name> activate [--enter <name_or_url_or_path>] [--volume 0.0-2.0]
    keyboard sound <name> deactivate
    keyboard sound status

<name> may be:
  - a built-in theme: thocky, creamy, clacky, clicky, marbly, silent, mechanical,
      fahh, gun_pistol, gun_shotgun, gun_sniper, gun_rifle
  - a direct http(s) URL to an audio file (your own custom click sound)
  - a path to a local audio file on disk

The chosen sound keeps playing on every keystroke until you explicitly run
`keyboard sound <name> deactivate` — closing the terminal does not stop it.
"""
import argparse
import os
import subprocess
import sys
import time

from . import player
from . import state as state_mod
from . import downloader

try:
    import psutil
except ImportError:
    psutil = None


def _is_url_or_path(name: str) -> bool:
    low = name.lower()
    return low.startswith("http://") or low.startswith("https://") or os.path.exists(name)


def _resolve_source(name: str):
    """Returns (display_name, theme_dir) for a built-in theme, URL, or local file."""
    low = name.lower()
    if low in player.BUILTIN_THEMES:
        return low, os.path.join(player.SOUNDS_DIR, low)
    if _is_url_or_path(name):
        print(f"⏬ Preparing custom sound from: {name}")
        theme_dir = downloader.prepare_custom_sound(name)
        display = name if len(name) <= 60 else (name[:57] + "...")
        return display, theme_dir
    valid = ", ".join(player.BUILTIN_THEMES)
    raise SystemExit(
        f"✗ Unknown sound '{name}'. Use a built-in theme ({valid}), an http(s) URL, "
        f"or a path to an existing audio file."
    )


def cmd_list(_args):
    state = state_mod.read_state()
    active_name = state.get("theme") if state else None
    print("Available keyboard sound themes:\n")
    for t in player.list_builtin_themes():
        marker = "  ●  ACTIVE" if active_name and active_name.lower() == t else ""
        print(f"  {t:<12} - {player.THEME_DESCRIPTIONS.get(t, '')}{marker}")
    print()
    if active_name and active_name.lower() not in player.BUILTIN_THEMES:
        print(f"Currently active custom sound: {active_name}\n")
    print("Activate with:   keyboard sound <name> activate")
    print("Deactivate with: keyboard sound <name> deactivate")


def cmd_status(_args):
    state = state_mod.read_state()
    if not state:
        print("No keyboard sound is currently active.")
        return
    alive = _pid_alive(state.get("pid"))
    status = "running" if alive else "stale (process not found)"
    print(f"Active theme : {state.get('theme')}")
    print(f"Status       : {status}")
    print(f"PID          : {state.get('pid')}")
    if state.get("enter_file"):
        print(f"Enter override: {state.get('enter_file')}")


def _pid_alive(pid):
    if not pid:
        return False
    if psutil is not None:
        return psutil.pid_exists(pid)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
    except AttributeError:
        return True


def _stop_pid(pid, timeout=4.0):
    if not pid:
        return
    if psutil is not None and psutil.pid_exists(pid):
        try:
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=timeout)
        except psutil.TimeoutExpired:
            try:
                p.kill()
            except Exception:
                pass
        except Exception:
            pass
        return
    # fallback without psutil
    try:
        import signal as sig

        os.kill(pid, getattr(sig, "SIGTERM", 15))
        deadline = time.time() + timeout
        while time.time() < deadline and _pid_alive(pid):
            time.sleep(0.1)
        if _pid_alive(pid):
            os.kill(pid, getattr(sig, "SIGKILL", 9))
    except OSError:
        pass


def cmd_activate(name, args):
    # Stop any currently active daemon first (only one active theme at a time).
    existing = state_mod.read_state()
    if existing and _pid_alive(existing.get("pid")):
        print(f"ℹ️  '{existing.get('theme')}' is active — switching sound...")
        _stop_pid(existing.get("pid"))
        state_mod.clear_state()

    display_name, theme_dir = _resolve_source(name)

    enter_file = None
    if args.enter:
        _, enter_dir = _resolve_source(args.enter)
        # Prefer a dedicated enter.wav (built-in themes have one tuned for
        # the Enter key); fall back to the theme's generic key sound
        # (always present for single-file custom sounds).
        dedicated = os.path.join(enter_dir, "enter.wav")
        generic = os.path.join(enter_dir, "key_00.wav")
        enter_file = dedicated if os.path.exists(dedicated) else generic

    log_path = state_mod.log_file()
    cmd = [
        sys.executable,
        "-m",
        "keyboard_sound.daemon",
        "--theme-dir",
        theme_dir,
        "--display-name",
        display_name,
        "--volume",
        str(args.volume),
    ]
    if enter_file:
        cmd += ["--enter-file", enter_file]

    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(
            subprocess, "DETACHED_PROCESS", 0
        )
    else:
        kwargs["start_new_session"] = True

    with open(log_path, "ab") as logf:
        subprocess.Popen(cmd, stdout=logf, stderr=logf, stdin=subprocess.DEVNULL, **kwargs)

    # wait for the daemon to report itself alive
    for _ in range(50):
        st = state_mod.read_state()
        if st and st.get("theme") == display_name:
            print(f"🔊 '{display_name}' keyboard sound ACTIVATED.")
            print("   Keep typing — it stays on until you run:")
            print(f"   keyboard sound {name} deactivate")
            return
        time.sleep(0.1)

    print(
        "⚠️  Could not confirm the sound engine started. Check the log for details:\n"
        f"   {log_path}\n"
        "   (On Linux this usually needs an X11 session for global key capture; "
        "on macOS grant 'Accessibility' / 'Input Monitoring' permission to your terminal.)"
    )


def cmd_deactivate(name, _args):
    state = state_mod.read_state()
    if not state:
        print("Nothing is currently active.")
        return
    active_theme = (state.get("theme") or "").lower()
    if name.lower() not in (active_theme, "all", "stop") and not _is_url_or_path(name):
        print(f"ℹ️  Note: currently active sound is '{state.get('theme')}', not '{name}'. Stopping it anyway.")
    _stop_pid(state.get("pid"))
    state_mod.clear_state()
    print(f"🔇 '{state.get('theme')}' keyboard sound DEACTIVATED.")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if len(argv) >= 1 and argv[0] == "sound":
        rest = argv[1:]
        if not rest:
            print(__doc__)
            return 0
        if rest[0] == "list":
            cmd_list(rest[1:])
            return 0
        if rest[0] == "status":
            cmd_status(rest[1:])
            return 0

        # pattern: <name> <activate|deactivate> [options]
        if len(rest) < 2:
            print("Usage: keyboard sound <name> activate|deactivate   (or: list / status)")
            return 1

        name = rest[0]
        action = rest[1].lower()
        extra = rest[2:]

        p = argparse.ArgumentParser(prog=f"keyboard sound {name} {action}")
        p.add_argument("--enter", default=None, help="override sound for the Enter key (theme/URL/path)")
        p.add_argument("--volume", type=float, default=1.0, help="playback volume, 0.0-2.0 (default 1.0)")
        args = p.parse_args(extra)

        if action == "activate":
            cmd_activate(name, args)
            return 0
        if action == "deactivate":
            cmd_deactivate(name, args)
            return 0

        print(f"Unknown action '{action}'. Use 'activate' or 'deactivate'.")
        return 1

    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
