"""Load and save non-secret settings from ``config/settings.json``."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from runtime_paths import resource_root, user_config_dir

from .schema import Settings, SettingsValidationError, default_settings, validate_settings

_CONFIG_DIR = user_config_dir()
SETTINGS_PATH = _CONFIG_DIR / "settings.json"
EXAMPLE_SETTINGS_PATH = resource_root() / "config" / "settings.example.json"


def load_settings(path: Path | None = None) -> Settings:
    """Return persisted settings, or defaults when the file is missing."""
    target = path or SETTINGS_PATH
    try:
        raw = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default_settings()
    except OSError as exc:
        raise SettingsValidationError("unable to read settings") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SettingsValidationError("settings file is not valid JSON") from exc
    return validate_settings(payload)


def save_settings(settings: Settings | dict[str, Any], path: Path | None = None) -> Settings:
    """Validate and write non-secret settings. Never stores API keys."""
    validated = settings if isinstance(settings, Settings) else validate_settings(settings)
    target = path or SETTINGS_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(validated.to_dict(), indent=2, ensure_ascii=False) + "\n"
    target.write_text(payload, encoding="utf-8")
    return validated


def ensure_settings_file(
    path: Path | None = None,
    *,
    example_path: Path | None = None,
) -> Settings:
    """Create ``settings.json`` from the example when missing; never clobber.

    Behavior:
    - Missing file → create from ``settings.example.json`` (validated defaults).
    - Existing valid file → return it unchanged (no rewrite).
    - Existing invalid JSON or schema → raise ``SettingsValidationError`` and
      leave the file untouched.

    Secrets are never written; only non-secret fields from the example / schema.
    """
    target = path or SETTINGS_PATH
    source = example_path or EXAMPLE_SETTINGS_PATH

    if target.exists():
        # Non-destructive: validate in place; never overwrite a bad file.
        return load_settings(target)

    validated = _load_example_settings(source)
    if _create_settings_exclusively(target, validated):
        return validated
    # Lost a create race; load the winner without rewriting it.
    return load_settings(target)


def _load_example_settings(source: Path) -> Settings:
    try:
        raw = source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SettingsValidationError(
            f"settings example file is missing: {source}"
        ) from exc
    except OSError as exc:
        raise SettingsValidationError("unable to read settings example") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SettingsValidationError(
            "settings example file is not valid JSON"
        ) from exc
    return validate_settings(payload)


def _create_settings_exclusively(target: Path, settings: Settings) -> bool:
    """Write settings only if ``target`` does not already exist.

    Returns True when this call created the file, False when it already existed.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(settings.to_dict(), indent=2, ensure_ascii=False) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(target, flags)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
    except Exception:
        # Best-effort cleanup of a partial create; never touch pre-existing files.
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return True
