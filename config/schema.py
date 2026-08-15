"""Typed non-secret settings schema.

API keys and other secrets must never appear in this schema or in
``settings.json``. Validate caller data and reject wrong types.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

PRIVACY_PROFILES = frozenset({"fully_local", "local_with_tools", "cloud", "hybrid"})
PROVIDER_IDS = frozenset({"gemini", "openai", "openrouter", "local"})
NETWORK_MODES = frozenset({"offline", "tools_only", "hybrid"})
OS_SYSTEMS = frozenset({"windows", "mac", "linux"})
MODEL_ROLE_KEYS = (
    "chat",
    "planning",
    "code",
    "vision",
    "embeddings",
    "stt",
    "tts",
)

DEFAULT_LANGUAGE = "ru"
DEFAULT_PRIVACY_PROFILE = "hybrid"
DEFAULT_PROVIDER_ID = "gemini"
DEFAULT_NETWORK_MODE = "hybrid"

_SECRET_FIELD_MARKERS = ("api_key", "token", "secret", "password")


class SettingsValidationError(ValueError):
    """Raised when settings data has the wrong type or an invalid value."""


def is_secret_field(name: str) -> bool:
    """Return True if a field name looks like a secret slot."""
    lowered = name.lower()
    return any(marker in lowered for marker in _SECRET_FIELD_MARKERS)


@dataclass(frozen=True)
class ModelRoles:
    """Placeholder model ids assigned to assistant roles."""

    chat: str = ""
    planning: str = ""
    code: str = ""
    vision: str = ""
    embeddings: str = ""
    stt: str = ""
    tts: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class Settings:
    """Non-secret application settings."""

    privacy_profile: str = DEFAULT_PRIVACY_PROFILE
    provider_id: str = DEFAULT_PROVIDER_ID
    language: str = DEFAULT_LANGUAGE
    network_mode: str = DEFAULT_NETWORK_MODE
    model_roles: ModelRoles = field(default_factory=ModelRoles)
    os_system: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "privacy_profile": self.privacy_profile,
            "provider_id": self.provider_id,
            "language": self.language,
            "network_mode": self.network_mode,
            "model_roles": self.model_roles.to_dict(),
        }
        if self.os_system is not None:
            payload["os_system"] = self.os_system
        return payload


def default_settings() -> Settings:
    return Settings()


def validate_settings(data: object) -> Settings:
    """Validate a mapping and return a ``Settings`` instance.

    Unknown required types and invalid enum values are rejected.
    Secret-like field names are rejected so keys cannot land in settings.
    Extra non-secret keys are ignored for forward compatibility.
    """
    if not isinstance(data, Mapping):
        raise SettingsValidationError("settings must be an object")

    for key in data:
        if not isinstance(key, str):
            raise SettingsValidationError("settings keys must be strings")
        if is_secret_field(key):
            raise SettingsValidationError(
                f"settings must not contain secret field {key!r}"
            )

    privacy_profile = _optional_enum(
        data, "privacy_profile", PRIVACY_PROFILES, DEFAULT_PRIVACY_PROFILE
    )
    provider_id = _optional_enum(data, "provider_id", PROVIDER_IDS, DEFAULT_PROVIDER_ID)
    language = _optional_non_empty_str(data, "language", DEFAULT_LANGUAGE)
    network_mode = _optional_enum(
        data, "network_mode", NETWORK_MODES, DEFAULT_NETWORK_MODE
    )
    model_roles = _validate_model_roles(data.get("model_roles", {}))
    os_system = _optional_os_overlay(data)

    return Settings(
        privacy_profile=privacy_profile,
        provider_id=provider_id,
        language=language,
        network_mode=network_mode,
        model_roles=model_roles,
        os_system=os_system,
    )


def _optional_enum(
    data: Mapping[str, Any],
    field_name: str,
    allowed: frozenset[str],
    default: str,
) -> str:
    if field_name not in data:
        return default
    value = data[field_name]
    if not isinstance(value, str):
        raise SettingsValidationError(f"{field_name} must be a string")
    if value not in allowed:
        raise SettingsValidationError(f"{field_name} has an unsupported value")
    return value


def _optional_non_empty_str(
    data: Mapping[str, Any], field_name: str, default: str
) -> str:
    if field_name not in data:
        return default
    value = data[field_name]
    if not isinstance(value, str):
        raise SettingsValidationError(f"{field_name} must be a string")
    if not value.strip():
        raise SettingsValidationError(f"{field_name} must be a non-empty string")
    return value


def _optional_os_overlay(data: Mapping[str, Any]) -> str | None:
    if "os_system" not in data:
        return None
    value = data["os_system"]
    if value is None:
        return None
    if not isinstance(value, str):
        raise SettingsValidationError("os_system must be a string")
    normalized = value.lower()
    if normalized not in OS_SYSTEMS:
        raise SettingsValidationError("os_system has an unsupported value")
    return normalized


def _validate_model_roles(value: object) -> ModelRoles:
    if value is None:
        return ModelRoles()
    if not isinstance(value, Mapping):
        raise SettingsValidationError("model_roles must be an object")

    kwargs: dict[str, str] = {}
    for key, role_value in value.items():
        if not isinstance(key, str):
            raise SettingsValidationError("model_roles keys must be strings")
        if is_secret_field(key):
            raise SettingsValidationError(
                f"model_roles must not contain secret field {key!r}"
            )
        if key not in MODEL_ROLE_KEYS:
            raise SettingsValidationError(f"model_roles contains unknown role {key!r}")
        if not isinstance(role_value, str):
            raise SettingsValidationError(f"model_roles.{key} must be a string")
        kwargs[key] = role_value
    return ModelRoles(**kwargs)
