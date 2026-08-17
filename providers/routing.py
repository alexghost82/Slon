"""Deterministic model routing with privacy and capability hard constraints."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

from providers.capabilities import supports
from providers.contracts import ModelInfo
from providers.errors import CapabilityError, ProviderError

CLOUD_PROVIDER_IDS = frozenset({"gemini", "openai", "openrouter"})
LOCAL_PROVIDER_IDS = frozenset({"local", "ollama", "llama_cpp"})
ROUTING_MODES = frozenset({"manual", "local_first", "local_only", "cloud_first"})

Availability = Mapping[object, bool] | None


def is_local_model(model: ModelInfo) -> bool:
    """Return whether a catalog entry belongs to a supported local runtime."""
    return model.provider_id in LOCAL_PROVIDER_IDS


def select_model(
    candidates: Sequence[ModelInfo],
    *,
    routing_mode: str,
    configured_provider_id: str,
    configured_model_id: str | None = None,
    required_role: str = "chat",
    required_capabilities: Collection[str] = (),
    availability: Availability = None,
    network_mode: str | None = None,
    privacy_profile: str | None = None,
) -> ModelInfo:
    """Select one model after eliminating every invalid candidate.

    Input order is the deterministic preference order within a routing tier.
    Cost/latency scoring intentionally belongs to W14-T13 and can reorder the
    already-valid candidates before calling this function.
    """
    if routing_mode not in ROUTING_MODES:
        raise ProviderError(f"unknown routing mode {routing_mode!r}")

    required = tuple(dict.fromkeys(required_capabilities))
    permitted = [
        model
        for model in candidates
        if _permitted(model, network_mode, privacy_profile)
        and _available(model, availability)
        and supports(model, required_role)
        and all(bool(getattr(model, name, False)) for name in required)
    ]

    if routing_mode == "manual":
        selected = next(
            (
                model
                for model in permitted
                if model.provider_id == configured_provider_id
                and (
                    configured_model_id is None
                    or model.model_id == configured_model_id
                )
            ),
            None,
        )
    elif routing_mode == "local_only":
        selected = next((model for model in permitted if is_local_model(model)), None)
    elif routing_mode == "local_first":
        selected = next((model for model in permitted if is_local_model(model)), None)
        if selected is None:
            selected = _preferred_provider(permitted, configured_provider_id)
    else:  # cloud_first
        clouds = [model for model in permitted if not is_local_model(model)]
        selected = _preferred_provider(clouds, configured_provider_id)
        if selected is None:
            selected = next(
                (model for model in permitted if is_local_model(model)), None
            )

    if selected is None:
        details = f"role {required_role!r}"
        if required:
            details += f" and capabilities {', '.join(required)}"
        if routing_mode == "local_only":
            details += " on an available local model"
        raise CapabilityError(
            f"no model satisfies {details} in routing mode {routing_mode!r}",
            provider_id=configured_provider_id,
            role=required_role,
            model_id=configured_model_id,
        )
    return selected


def _preferred_provider(
    candidates: Sequence[ModelInfo], provider_id: str
) -> ModelInfo | None:
    return next(
        (model for model in candidates if model.provider_id == provider_id),
        candidates[0] if candidates else None,
    )


def _permitted(
    model: ModelInfo, network_mode: str | None, privacy_profile: str | None
) -> bool:
    if network_mode in {"offline", "tools_only"} or privacy_profile in {
        "fully_local",
        "local_with_tools",
    }:
        return is_local_model(model)
    return True


def _available(model: ModelInfo, availability: Availability) -> bool:
    if availability is None:
        return True
    keys = (
        (model.provider_id, model.model_id),
        f"{model.provider_id}:{model.model_id}",
        model.model_id,
        model.provider_id,
    )
    return next((bool(availability[key]) for key in keys if key in availability), False)


__all__ = [
    "CLOUD_PROVIDER_IDS",
    "LOCAL_PROVIDER_IDS",
    "ROUTING_MODES",
    "is_local_model",
    "select_model",
]
