"""py2app configuration for the standalone Slon macOS bundle."""

from __future__ import annotations

from pathlib import Path

from setuptools import setup

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "build" / "macos"
ICON_FILE = BUILD_DIR / "Slon.icns"


def files_under(source: Path, destination: str) -> list[tuple[str, list[str]]]:
    if not source.is_dir():
        return []
    groups: list[tuple[str, list[str]]] = []
    for directory in sorted(path for path in source.rglob("*") if path.is_dir()):
        files = sorted(str(path) for path in directory.iterdir() if path.is_file())
        if files:
            relative = directory.relative_to(source)
            target = str(Path(destination) / relative)
            groups.append((target, files))
    root_files = sorted(str(path) for path in source.iterdir() if path.is_file())
    if root_files:
        groups.insert(0, (destination, root_files))
    return groups


data_files = [
    ("", [str(ROOT / "logo.png")]),
    ("config", [str(ROOT / "config" / "settings.example.json")]),
    ("core", [str(ROOT / "core" / "prompt.txt")]),
    *files_under(ROOT / "i18n", "i18n"),
]

# Piper is optional and gitignored. Include a locally provisioned voice when
# present, but never include TLS private keys or unrelated model directories.
data_files.extend(files_under(ROOT / "models" / "piper", "models/piper"))

options = {
    "argv_emulation": False,
    "iconfile": str(ICON_FILE),
    "packages": [
        "actions",
        "agent",
        "config",
        "localization",
        "mark",
        "memory",
        "policies",
        "providers",
        "server",
        "speech",
    ],
    "includes": ["runtime_paths", "ui"],
    "excludes": ["tkinter", "test", "tests"],
    "plist": {
        "CFBundleName": "Slon",
        "CFBundleDisplayName": "Slon",
        "CFBundleIdentifier": "local.slon.desktop",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
        "NSMicrophoneUsageDescription": (
            "Slon uses the microphone for wake-word detection and voice commands."
        ),
        "NSCameraUsageDescription": (
            "Slon uses the camera only when you ask it to analyze a camera image."
        ),
        "NSAppleEventsUsageDescription": (
            "Slon uses automation to control applications when you explicitly request it."
        ),
    },
}

setup(
    name="Slon",
    version="0.1.0",
    app=[str(ROOT / "main.py")],
    data_files=data_files,
    options={"py2app": options},
)
