"""Offline tests for first-run settings.json bootstrap."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from config.schema import SettingsValidationError, validate_settings
from config.settings import (
    EXAMPLE_SETTINGS_PATH,
    ensure_settings_file,
    load_settings,
)


def test_missing_settings_creates_validated_example_defaults(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    assert not target.exists()

    settings = ensure_settings_file(target)

    assert target.is_file()
    assert settings.language == "ru"
    assert settings.privacy_profile == "hybrid"
    assert settings.provider_id == "gemini"
    assert settings.network_mode == "hybrid"
    assert settings.model_roles.to_dict() == {
        "chat": "",
        "planning": "",
        "code": "",
        "vision": "",
        "embeddings": "",
        "stt": "",
        "tts": "",
    }

    on_disk = json.loads(target.read_text(encoding="utf-8"))
    assert validate_settings(on_disk) == settings
    assert "api_key" not in json.dumps(on_disk).lower()
    assert "token" not in json.dumps(on_disk).lower()
    assert "secret" not in json.dumps(on_disk).lower()
    assert "password" not in json.dumps(on_disk).lower()


def test_existing_settings_are_not_overwritten(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    original = {
        "privacy_profile": "cloud",
        "provider_id": "openai",
        "language": "en",
        "network_mode": "hybrid",
        "model_roles": {
            "chat": "keep-me",
            "planning": "",
            "code": "",
            "vision": "",
            "embeddings": "",
            "stt": "",
            "tts": "",
        },
    }
    target.write_text(
        json.dumps(original, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    before = target.read_text(encoding="utf-8")

    settings = ensure_settings_file(target)

    assert target.read_text(encoding="utf-8") == before
    assert settings.language == "en"
    assert settings.provider_id == "openai"
    assert settings.privacy_profile == "cloud"
    assert settings.model_roles.chat == "keep-me"


def test_invalid_existing_json_raises_without_clobber(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    broken = "{not-json"
    target.write_text(broken, encoding="utf-8")

    with pytest.raises(SettingsValidationError, match="not valid JSON"):
        ensure_settings_file(target)

    assert target.read_text(encoding="utf-8") == broken


def test_invalid_existing_schema_raises_without_clobber(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    payload = json.dumps({"privacy_profile": "not-a-profile"}, indent=2) + "\n"
    target.write_text(payload, encoding="utf-8")

    with pytest.raises(SettingsValidationError, match="privacy_profile"):
        ensure_settings_file(target)

    assert target.read_text(encoding="utf-8") == payload


def test_custom_example_path_is_used_when_creating(tmp_path: Path) -> None:
    example = tmp_path / "custom.example.json"
    target = tmp_path / "out" / "settings.json"
    example.write_text(
        json.dumps(
            {
                "privacy_profile": "fully_local",
                "provider_id": "local",
                "language": "ru",
                "network_mode": "offline",
                "model_roles": {
                    "chat": "",
                    "planning": "",
                    "code": "",
                    "vision": "",
                    "embeddings": "",
                    "stt": "",
                    "tts": "",
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    settings = ensure_settings_file(target, example_path=example)

    assert settings.privacy_profile == "fully_local"
    assert settings.provider_id == "local"
    assert settings.network_mode == "offline"
    assert load_settings(target) == settings


def test_repo_example_path_exists_and_matches_defaults() -> None:
    assert EXAMPLE_SETTINGS_PATH.is_file()
    example = json.loads(EXAMPLE_SETTINGS_PATH.read_text(encoding="utf-8"))
    settings = validate_settings(example)
    assert settings.language == "ru"
    assert settings.privacy_profile == "hybrid"
    assert settings.provider_id == "gemini"
