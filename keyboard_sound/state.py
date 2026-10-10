"""Cross-platform locations for pid file / state file / logs / cached custom sounds."""
import os
import sys
import json

APP_NAME = "keyboard-sound"


def _base_config_dir() -> str:
    if sys.platform == "win32":
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(root, APP_NAME)
    if sys.platform == "darwin":
        return os.path.expanduser(f"~/Library/Application Support/{APP_NAME}")
    # Linux / other unix
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(xdg, APP_NAME)


def config_dir() -> str:
    d = _base_config_dir()
    os.makedirs(d, exist_ok=True)
    return d


def state_file() -> str:
    return os.path.join(config_dir(), "state.json")


def log_file() -> str:
    return os.path.join(config_dir(), "daemon.log")


def custom_sounds_dir() -> str:
    d = os.path.join(config_dir(), "custom_sounds")
    os.makedirs(d, exist_ok=True)
    return d


def read_state():
    path = state_file()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def write_state(data: dict):
    path = state_file()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def clear_state():
    path = state_file()
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
