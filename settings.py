import os
import json

SETTINGS_FILE = "settings.json"
HISTORY_FILE = "history.json"
DEFAULT_SETTINGS = {
    "dark_mode": False,
    "default_download_path": os.path.expanduser("~"),
    "default_format": "mp4",
    "default_quality": "1080p (?? MB) [mp4]",
    "default_sub_lang": "Otomatik",
    "language": "Türkçe"
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def clear_history():
    save_history([])
