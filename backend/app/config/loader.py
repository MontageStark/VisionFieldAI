from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Any

import yaml

from .settings import Settings

_CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "configs"
_settings_instance: Settings | None = None
_lock = Lock()


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a single YAML file and return its contents as a dict."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _load_all_yaml_configs(configs_dir: Path | None = None) -> dict[str, Any]:
    """Load and merge all YAML config files from the configs directory.

    Files are merged in alphabetical order so that later files override
    earlier ones for overlapping keys.
    """
    if configs_dir is None:
        configs_dir = _CONFIGS_DIR

    if not configs_dir.exists():
        return {}

    merged: dict[str, Any] = {}
    yaml_files = sorted(configs_dir.glob("*.yaml"))
    for yaml_file in yaml_files:
        file_data = _load_yaml_file(yaml_file)
        for key, value in file_data.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key].update(value)
            else:
                merged[key] = value
    return merged


def _apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    """Apply environment variable overrides to the config dict.

    Environment variables use __ as the nested delimiter.
    For example: AI__DEVICE=cpu overrides data["ai"]["device"].
    """
    for env_key, env_value in os.environ.items():
        if "__" not in env_key:
            continue
        parts = env_key.lower().split("__")
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            if not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = _coerce_env_value(env_value)
    return data


def _coerce_env_value(value: str) -> Any:
    """Coerce an environment variable string value to its appropriate type."""
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    if value.lower() in ("none", "null", ""):
        return ""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def load_settings(
    configs_dir: Path | None = None,
    use_env_overrides: bool = True,
) -> Settings:
    """Load settings from YAML files with optional environment variable overrides.

    Args:
        configs_dir: Directory containing YAML config files.
            Defaults to the project-level configs/ directory.
        use_env_overrides: Whether to apply environment variable overrides.

    Returns:
        A Settings instance with values loaded from YAML and env vars.
    """
    data = _load_all_yaml_configs(configs_dir)
    if use_env_overrides:
        data = _apply_env_overrides(data)
    return Settings(**data)


def get_settings(configs_dir: Path | None = None, force_reload: bool = False) -> Settings:
    """Get the singleton Settings instance.

    Creates the instance on first call, returns cached on subsequent calls.
    Use force_reload=True to reload from disk.

    Args:
        configs_dir: Directory containing YAML config files.
        force_reload: If True, reload settings from disk.

    Returns:
        The singleton Settings instance.
    """
    global _settings_instance
    with _lock:
        if _settings_instance is None or force_reload:
            _settings_instance = load_settings(configs_dir)
    return _settings_instance


def reset_settings() -> None:
    """Reset the singleton settings instance.

    Useful for testing to ensure a fresh instance.
    """
    global _settings_instance
    with _lock:
        _settings_instance = None
