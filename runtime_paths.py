"""Resolve bundled resources and writable per-user application data."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Slon"


def resource_root() -> Path:
    """Return the source tree or the Resources directory of a frozen app."""
    if getattr(sys, "frozen", False):
        resource_path = os.environ.get("RESOURCEPATH")
        if resource_path:
            return Path(resource_path).resolve()
        executable = Path(sys.executable).resolve()
        if executable.parent.name == "MacOS":
            return executable.parent.parent / "Resources"
        return executable.parent
    return Path(__file__).resolve().parent


def user_data_root() -> Path:
    """Return a writable root for settings, memory, and downloaded models."""
    override = os.environ.get("SLON_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if not getattr(sys, "frozen", False):
        return resource_root()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "slon"


def user_config_dir() -> Path:
    return user_data_root() / "config"


def user_memory_dir() -> Path:
    return user_data_root() / "memory"
