from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import replace

import pytest

from providers.contracts import (
    ChatEvent,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ModelInfo,
    ProviderStatus,
    ToolDefinition,
)
from providers.errors import CapabilityError, ProviderAuthError, ProviderError
from providers.registry import register

from providers.router import NeverFallbackPolicy, Router
from tests.unit.providers.mocks import MockChatProvider, mock_model

USER_TEXT = "router ping"


class RecordingProvider:
    """Chat stand-in that records calls before doing any work."""

    def __init__(self, provider_id: str, text: str = "ok") -> None:
        self.provider_id = provider_id
        self.text = text
        self.chat_calls = 0
        self.stream_calls = 0
        self.requests: list[ChatRequest] = []

    async def list_models(self) -> list[ModelInfo]:
        return [mock_model(self.provider_id)]

    async def validate(self) -> ProviderStatus:
        return ProviderStatus(provider_id=self.provider_id, ok=True, message="ok")

    async def chat(self, request: ChatRequest) -> ChatResponse:
        self.chat_calls += 1
        self.requests.append(request)
        return ChatResponse(
            text=self.text,
            provider_id=self.provider_id,
            model_id=request.model.model_id,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatEvent]:
        self.stream_calls += 1
        self.requests.append(request)
        yield ChatEvent(type="delta", text=self.text)
        yield ChatEvent(type="done")


class FailingProvider:
    def __init__(
        self,
        provider_id: str,
        error: Exception | None = None,
    ) -> None:
        self.provider_id = provider_id
        self.error = error or ProviderError("local boom", provider_id=provider_id)
        self.chat_calls = 0
        self.stream_calls = 0

    async def list_models(self) -> list[ModelInfo]:
        return [mock_model(self.provider_id)]

    async def validate(self) -> ProviderStatus:
        return ProviderStatus(provider_id=self.provider_id, ok=False, message="fail")

    async def chat(self, request: ChatRequest) -> ChatResponse:
        self.chat_calls += 1
        raise self.error

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatEvent]:
        self.stream_calls += 1
        raise self.error
        yield ChatEvent(type="done")  # pragma: no cover


class ToProvider:
    name = "to_provider"

    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id

    def next(self, failed_provider_id: str, error: BaseException) -> str | None:
        return self.provider_id


def _request(
    provider_id: str = "local",
    *,
    role: str = "chat",
    text: bool = True,
    streaming: bool = True,
    tool_calling: bool = False,
    with_tools: bool = False,
) -> ChatRequest:
    base_model = mock_model(provider_id, text=text, streaming=streaming)
    model = replace(base_model, tool_calling=tool_calling)
    return ChatRequest(
        model=model,
        messages=(ChatMessage(role="user", content=USER_TEXT),),
        role=role,
        tools=(
            ToolDefinition(
                name="lookup",
                description="Look up a value",
                parameters={"type": "object", "properties": {}},
            ),
        )
        if with_tools
        else (),
    )


async def test_routes_chat_to_injected_provider() -> None:
    provider = RecordingProvider("local", text="from-local")
    router = Router(provider_id="local", providers={"local": provider})
    request = _request("local")
    response = await router.chat(request)
    assert provider.chat_calls == 1
    assert provider.requests[0] is request
    assert response.text == "from-local"
    assert response.provider_id == "local"
    assert response.model_id == request.model.model_id


async def test_capability_failure_does_not_call_provider() -> None:
    provider = RecordingProvider("openai")
    router = Router(provider_id="openai", providers={"openai": provider})
    request = _request("openai", text=False)
    with pytest.raises(CapabilityError) as exc_info:
        await router.chat(request)
    assert provider.chat_calls == 0
    assert exc_info.value.role == "chat"
    assert exc_info.value.model_id == request.model.model_id


async def test_text_only_chat_without_tools_reaches_provider() -> None:
    provider = RecordingProvider("local")
    router = Router(provider_id="local", providers={"local": provider})
    await router.chat(_request("local", text=True, tool_calling=False))
    assert provider.chat_calls == 1


async def test_text_only_model_with_tools_fails_before_provider_call() -> None:
    provider = RecordingProvider("local")
    router = Router(provider_id="local", providers={"local": provider})
    request = _request("local", text=True, tool_calling=False, with_tools=True)
    with pytest.raises(CapabilityError, match="tool_calling"):
        await router.chat(request)
    assert provider.chat_calls == 0


async def test_text_only_model_with_tools_fails_before_provider_stream() -> None:
    provider = RecordingProvider("local")
    router = Router(provider_id="local", providers={"local": provider})
    request = _request("local", text=True, tool_calling=False, with_tools=True)
    with pytest.raises(CapabilityError, match="tool_calling"):
        async for _event in router.stream(request):
            pytest.fail("capability failure must occur before streaming")
    assert provider.stream_calls == 0


async def test_tool_capable_model_with_tools_reaches_provider() -> None:
    provider = RecordingProvider("local")
    router = Router(provider_id="local", providers={"local": provider})
    request = _request("local", text=True, tool_calling=True, with_tools=True)
    await router.chat(request)
    assert provider.chat_calls == 1
    assert provider.requests == [request]


async def test_default_policy_never_falls_back() -> None:
    local = FailingProvider("local")
    cloud = RecordingProvider("gemini")
    router = Router(
        provider_id="local",
        network_mode="hybrid",
        privacy_profile="hybrid",
        providers={"local": local, "gemini": cloud},
    )
    assert NeverFallbackPolicy().next("local", ProviderError("x")) is None
    with pytest.raises(ProviderError, match="local boom"):
        await router.chat(_request("local"))
    assert local.chat_calls == 1
    assert cloud.chat_calls == 0


@pytest.mark.parametrize(
    "constraint",
    [{"network_mode": "offline"}, {"privacy_profile": "fully_local"}],
)
@pytest.mark.parametrize("cloud_id", ["gemini", "openai", "openrouter"])
async def test_offline_and_fully_local_refuse_cloud(
    constraint: dict[str, str], cloud_id: str
) -> None:
    cloud = RecordingProvider(cloud_id)
    router = Router(
        provider_id=cloud_id,
        providers={cloud_id: cloud},
        network_mode=constraint.get("network_mode"),
        privacy_profile=constraint.get("privacy_profile"),
    )
    with pytest.raises(ProviderError, match="not allowed") as exc_info:
        await router.chat(_request(cloud_id))
    assert cloud.chat_calls == 0
    assert exc_info.value.provider_id == cloud_id
    status = await router.validate()
    assert status.ok is False
    assert status.provider_id == cloud_id


async def test_local_failure_in_offline_does_not_call_cloud_mock() -> None:
    local = FailingProvider("local")
    cloud = RecordingProvider("gemini")
    router = Router(
        provider_id="local",
        network_mode="offline",
        fallback_policy=ToProvider("gemini"),
        providers={"local": local, "gemini": cloud},
    )
    with pytest.raises(ProviderError, match="local boom"):
        await router.chat(_request("local"))
    assert local.chat_calls == 1
    assert cloud.chat_calls == 0


async def test_local_failure_in_fully_local_does_not_call_cloud_mock() -> None:
    local = FailingProvider("local")
    cloud = RecordingProvider("openrouter")
    router = Router(
        provider_id="local",
        privacy_profile="fully_local",
        fallback_policy=ToProvider("openrouter"),
        providers={"local": local, "openrouter": cloud},
    )
    with pytest.raises(ProviderError, match="local boom"):
        await router.chat(_request("local"))
    assert cloud.chat_calls == 0


async def test_stream_yields_chat_events() -> None:
    provider = MockChatProvider("local")
    router = Router(provider_id="local", providers={"local": provider})
    events = [event async for event in router.stream(_request("local"))]
    assert events
    assert all(isinstance(event, ChatEvent) for event in events)
    assert {event.type for event in events} <= {"delta", "done"}
    assert events[-1].type == "done"
    assert events[-1].text == ""
    assert provider.stream_calls == 1


async def test_explicit_policy_retries_once_when_allowed() -> None:
    local = FailingProvider("local")
    cloud = RecordingProvider("openai", text="from-openai")
    request = _request("local")
    router = Router(
        provider_id="local",
        network_mode="hybrid",
        privacy_profile="hybrid",
        fallback_policy=ToProvider("openai"),
        providers={"local": local, "openai": cloud},
    )
    response = await router.chat(request)
    assert local.chat_calls == 1
    assert cloud.chat_calls == 1
    assert cloud.requests[0] is request
    assert response.text == "from-openai"
    assert response.model_id == request.model.model_id


async def test_missing_key_raises_without_calling_factory(clean_registry) -> None:
    calls = {"n": 0}

    def factory(api_key: str | None = None) -> RecordingProvider:
        calls["n"] += 1
        raise AssertionError("cloud factory must not run without a key")

    register("openai", factory)
    router = Router(provider_id="openai", key_provider=lambda _pid: None)
    request = ChatRequest(
        model=ModelInfo(
            provider_id="openai",
            model_id="gpt-test",
            display_name="gpt test",
            text=True,
        ),
        messages=(ChatMessage(role="user", content=USER_TEXT),),
        role="chat",
    )
    with pytest.raises(ProviderAuthError, match="missing api key") as exc_info:
        await router.chat(request)
    assert calls["n"] == 0
    assert exc_info.value.provider_id == "openai"
    status = await router.validate()
    assert status.ok is False
    assert "missing" in status.message.lower()
    assert calls["n"] == 0


async def test_blank_key_is_treated_as_missing(clean_registry) -> None:
    calls = {"n": 0}

    def factory(api_key: str | None = None) -> RecordingProvider:
        calls["n"] += 1
        return RecordingProvider("gemini")

    register("gemini", factory)
    router = Router(provider_id="gemini", key_provider=lambda _pid: "   ")
    with pytest.raises(ProviderAuthError):
        await router.chat(_request("gemini"))
    assert calls["n"] == 0
