from __future__ import annotations

from pathlib import Path

import runtime_paths

ROOT = Path(__file__).resolve().parents[3]


def test_source_mode_keeps_existing_repo_data_layout() -> None:
    assert runtime_paths.resource_root() == ROOT
    assert runtime_paths.user_data_root() == ROOT


def test_data_dir_override_is_respected(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target = tmp_path / "Slon Data"
    monkeypatch.setenv("SLON_DATA_DIR", str(target))
    assert runtime_paths.user_data_root() == target
    assert runtime_paths.user_config_dir() == target / "config"
    assert runtime_paths.user_memory_dir() == target / "memory"


def test_frozen_macos_paths_use_resources_and_application_support(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resources = tmp_path / "Slon.app" / "Contents" / "Resources"
    home = tmp_path / "home"
    monkeypatch.setattr(runtime_paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(runtime_paths.sys, "platform", "darwin")
    monkeypatch.setenv("RESOURCEPATH", str(resources))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("SLON_DATA_DIR", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    assert runtime_paths.resource_root() == resources.resolve()
    assert runtime_paths.user_data_root() == home / "Library" / "Application Support" / "Slon"


def test_macos_packaging_files_exist() -> None:
    expected = (
        ROOT / "packaging" / "macos" / "setup.py",
        ROOT / "packaging" / "macos" / "build_app.py",
        ROOT / "packaging" / "macos" / "entitlements.plist",
        ROOT / "requirements-packaging-macos.txt",
    )
    assert all(path.is_file() for path in expected)


def test_bundle_identifier_and_privacy_descriptions_are_configured() -> None:
    setup_source = (ROOT / "packaging" / "macos" / "setup.py").read_text(
        encoding="utf-8"
    )
    assert '"CFBundleIdentifier": "local.slon.desktop"' in setup_source
    assert '"NSMicrophoneUsageDescription"' in setup_source
    assert '"NSCameraUsageDescription"' in setup_source
    assert '"NSAppleEventsUsageDescription"' in setup_source
