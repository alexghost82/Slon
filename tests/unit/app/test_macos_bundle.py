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


def test_signing_handles_nested_macho_files_before_the_bundle() -> None:
    build_source = (ROOT / "packaging" / "macos" / "build_app.py").read_text(
        encoding="utf-8"
    )
    assert "def sign_app_bundle()" in build_source
    assert 'run("codesign", "--force", "--sign", "-", str(path))' in build_source
    assert 'run("codesign", "--verify", "--deep", "--strict"' in build_source


def test_codex_run_action_uses_project_build_and_run_script() -> None:
    run_script = ROOT / "script" / "build_and_run.sh"
    environment = ROOT / ".codex" / "environments" / "environment.toml"
    assert run_script.is_file()
    assert environment.is_file()
    assert "packaging/macos/build_app.py" in run_script.read_text(encoding="utf-8")
    assert 'command = "./script/build_and_run.sh"' in environment.read_text(
        encoding="utf-8"
    )


def test_py2app_package_roots_are_regular_python_packages() -> None:
    for package in ("actions", "agent", "mark", "speech"):
        assert (ROOT / package / "__init__.py").is_file()


def test_translations_resolve_from_runtime_resource_root() -> None:
    translator_source = (ROOT / "localization" / "translator.py").read_text(
        encoding="utf-8"
    )
    assert 'resource_root() / "i18n"' in translator_source
