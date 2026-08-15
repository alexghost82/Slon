from __future__ import annotations

import pytest

from config.schema import (
    DEFAULT_LANGUAGE,
    SettingsValidationError,
    default_settings,
    validate_settings,
)


def test_defaults_use_russian_language():
    settings = validate_settings({})
    assert settings.language == DEFAULT_LANGUAGE == "ru"
    assert settings.privacy_profile == "hybrid"
    assert settings.provider_id == "gemini"
    assert settings.network_mode == "hybrid"
    assert settings.os_system is None


def test_rejects_invalid_privacy_profile_type():
    with pytest.raises(SettingsValidationError, match="privacy_profile"):
        validate_settings({"privacy_profile": 1})


def test_rejects_unknown_privacy_profile():
    with pytest.raises(SettingsValidationError, match="privacy_profile"):
        validate_settings({"privacy_profile": "unknown-profile"})


def test_rejects_invalid_provider_type():
    with pytest.raises(SettingsValidationError, match="provider_id"):
        validate_settings({"provider_id": ["gemini"]})


def test_rejects_unknown_provider():
    with pytest.raises(SettingsValidationError, match="provider_id"):
        validate_settings({"provider_id": "not-a-provider"})


def test_rejects_invalid_language_type():
    with pytest.raises(SettingsValidationError, match="language"):
        validate_settings({"language": None})


def test_rejects_invalid_network_mode_type():
    with pytest.raises(SettingsValidationError, match="network_mode"):
        validate_settings({"network_mode": 0})


def test_rejects_invalid_model_roles_type():
    with pytest.raises(SettingsValidationError, match="model_roles"):
        validate_settings({"model_roles": "chat"})


def test_rejects_non_string_model_role():
    with pytest.raises(SettingsValidationError, match="model_roles.chat"):
        validate_settings({"model_roles": {"chat": 12}})


def test_rejects_unknown_model_role():
    with pytest.raises(SettingsValidationError, match="unknown role"):
        validate_settings({"model_roles": {"music": ""}})


def test_rejects_secret_fields():
    with pytest.raises(SettingsValidationError, match="secret field"):
        validate_settings({"gemini_api_key": "should-not-be-here"})


def test_rejects_invalid_os_system_type():
    with pytest.raises(SettingsValidationError, match="os_system"):
        validate_settings({"os_system": 3})


def test_rejects_non_object_payload():
    with pytest.raises(SettingsValidationError, match="object"):
        validate_settings(["not", "an", "object"])


def test_default_settings_round_trip():
    assert default_settings() == validate_settings(default_settings().to_dict())
