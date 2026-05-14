from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clfc.core.index import SCHEMA_VERSION, clfc_data_root

BOOLEAN_KEYS = {"dangerously_skip_permissions", "allow_dangerously_skip_permissions"}
STRING_KEYS = {"model", "effort", "permission_mode"}
PERMISSION_MODES = {"acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"}
EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}


def default_settings() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "defaults": {
            "model": None,
            "effort": None,
            "permission_mode": None,
            "dangerously_skip_permissions": False,
            "allow_dangerously_skip_permissions": False,
        },
    }


def settings_path(data_root: Path | None = None) -> Path:
    return (data_root or clfc_data_root()).expanduser().resolve() / "settings.json"


def load_settings(data_root: Path | None = None) -> dict[str, Any]:
    path = settings_path(data_root)
    settings = default_settings()
    if not path.exists():
        return settings
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return settings
    if not isinstance(loaded, dict):
        return settings
    defaults = loaded.get("defaults")
    if isinstance(defaults, dict):
        settings["defaults"].update({key: defaults.get(key) for key in settings["defaults"].keys() if key in defaults})
    return settings


def save_settings(settings: dict[str, Any], data_root: Path | None = None) -> Path:
    path = settings_path(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def set_default(key: str, value: str, data_root: Path | None = None) -> dict[str, Any]:
    normalized_key = normalize_key(key)
    settings = load_settings(data_root)
    defaults = settings["defaults"]

    if normalized_key in BOOLEAN_KEYS:
        defaults[normalized_key] = parse_bool(value)
    elif normalized_key in STRING_KEYS:
        defaults[normalized_key] = parse_nullable_string(normalized_key, value)
    else:
        allowed = sorted(BOOLEAN_KEYS | STRING_KEYS)
        raise ValueError(f"Unknown setting {key!r}. Allowed settings: {', '.join(allowed)}")

    save_settings(settings, data_root)
    return settings


def normalize_key(key: str) -> str:
    return key.strip().replace("-", "_")


def parse_bool(value: str) -> bool:
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "yes", "y", "on", "enable", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "disable", "disabled"}:
        return False
    raise ValueError(f"Expected a boolean value such as on/off, got {value!r}.")


def parse_nullable_string(key: str, value: str) -> str | None:
    normalized = value.strip()
    if normalized.casefold() in {"none", "null", "clear", "unset"}:
        return None
    if key == "permission_mode" and normalized not in PERMISSION_MODES:
        raise ValueError(f"Unknown permission mode {value!r}. Allowed: {', '.join(sorted(PERMISSION_MODES))}")
    if key == "effort" and normalized not in EFFORT_LEVELS:
        raise ValueError(f"Unknown effort {value!r}. Allowed: {', '.join(sorted(EFFORT_LEVELS))}")
    return normalized
