import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
VOICE_PRESETS_FILE = CONFIG_DIR / "voice_presets.json"

DEFAULT_SETTINGS = {
    "host": "0.0.0.0",
    "port": 9880,
    "api_key": "sk-edge-tts-local",
    "default_voice": "zh-CN-XiaoxiaoNeural",
    "require_auth": False,
}


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    _ensure_config_dir()
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()
    with SETTINGS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    merged = DEFAULT_SETTINGS.copy()
    merged.update(data)
    return merged


def save_settings(settings: dict) -> None:
    _ensure_config_dir()
    merged = DEFAULT_SETTINGS.copy()
    merged.update(settings)
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)


def load_voice_presets() -> list[dict]:
    if not VOICE_PRESETS_FILE.exists():
        return []
    with VOICE_PRESETS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("presets", [])


def update_default_voice(voice: str) -> dict:
    settings = load_settings()
    settings["default_voice"] = voice
    save_settings(settings)
    return settings
