"""Shared ChatProvider behavior for loopback local runtimes."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from providers.capabilities import require_capability
from providers.contracts import (
    ChatEvent,
    ChatRequest,
    ChatResponse,
    ModelInfo,
    ProviderStatus,
    ToolCall,
)
from providers.errors import (
    CapabilityError,
    ProviderAuthError,
    ProviderError,
    ProviderOfflineError,
)
from providers.local.endpoint import assert_endpoint_allowed, join_endpoint
from providers.local.http import StdlibTransport, Transport, TransportResponse

DEFAULT_LOCAL_BASE_URL = "http://127.0.0.1:8080/v1"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_LLAMA_CPP_BASE_URL = "http://127.0.0.1:8080"
DEFAULT_TIMEOUT = 30.0
PROTOCOL_OPENAI = "openai"
PROTOCOL_OLLAMA = "ollama"


class BaseLocalChatProvider:
    """Loopback-first chat adapter. Failures never fall back to cloud."""

    provider_id: str = "local"
    default_base_url: str = DEFAULT_LOCAL_BASE_URL
    models_path: str = "/v1/models"
    chat_path: str = "/v1/chat/completions"
    protocol: str = PROTOCOL_OPENAI

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        *,
        allow_remote: bool = False,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.allow_remote = allow_remote
        self._transport = transport if transport is not None else StdlibTransport()
        assert_endpoint_allowed(
            self.base_url,
            allow_remote=self.allow_remote,
            provider_id=self.provider_id,
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(base_url={self.base_url!r}, "
            f"allow_remote={self.allow_remote})"
        )

    async def validate(self) -> ProviderStatus:
        assert_endpoint_allowed(
            self.base_url,
            allow_remote=self.allow_remote,
            provider_id=self.provider_id,
        )
        try:
            await self.list_models()
        except ProviderError as exc:
            return ProviderStatus(
                provider_id=self.provider_id,
                ok=False,
                message=str(exc),
            )
        return ProviderStatus(provider_id=self.provider_id, ok=True)

    async def list_models(self) -> list[ModelInfo]:
        response = self._request("GET", self.models_path)
        self._raise_http(response)
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "local runtime returned an invalid models payload",
                provider_id=self.provider_id,
            ) from exc
        return self._parse_models(payload)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        require_capability(request.model, request.role)
        self._require_tool_capability(request)
        response = self._request(
            "POST",
            self.chat_path,
            json_body=self._chat_payload(request, stream=False),
        )
        self._raise_http(response)
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "local runtime returned an invalid chat payload",
                provider_id=self.provider_id,
            ) from exc
        text, tool_calls = self._parse_chat_message(payload)
        return ChatResponse(
            text=text,
            provider_id=self.provider_id,
            model_id=request.model.model_id,
            tool_calls=tool_calls,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatEvent]:
        require_capability(request.model, request.role)
        self._require_tool_capability(request)
        if request.tools and self.protocol == PROTOCOL_OLLAMA:
            response = await self.chat(request)
            if response.text:
                yield ChatEvent(type="delta", text=response.text)
            for tool_call in response.tool_calls:
                yield ChatEvent(type="tool_call", tool_call=tool_call)
            yield ChatEvent(type="done")
            return
        response = self._request(
            "POST",
            self.chat_path,
            json_body=self._chat_payload(request, stream=True),
            stream=True,
        )
        self._raise_http(response)
        if self.protocol == PROTOCOL_OLLAMA:
            async for event in self._iter_ollama_stream(response):
                yield event
        else:
            async for event in self._iter_openai_stream(response):
                yield event
        yield ChatEvent(type="done")

    def _chat_payload(self, request: ChatRequest, *, stream: bool) -> dict[str, object]:
        messages = [
            {"role": message.role, "content": message.content}
            for message in request.messages
        ]
        payload: dict[str, object] = {
            "model": request.model.model_id,
            "messages": messages,
            "stream": stream,
        }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": dict(tool.parameters),
                    },
                }
                for tool in request.tools
            ]
            # Ollama's native /api/chat contract supports tools, but does not
            # define OpenAI's tool_choice field.
            if request.tool_choice is not None and self.protocol != PROTOCOL_OLLAMA:
                payload["tool_choice"] = request.tool_choice
        return payload

    def _require_tool_capability(self, request: ChatRequest) -> None:
        if request.tools and not request.model.tool_calling:
            raise CapabilityError(
                f"model {request.model.model_id!r} does not support tool calling",
                provider_id=request.model.provider_id,
                role=request.role,
                model_id=request.model.model_id,
            )

    def _parse_models(self, payload: object) -> list[ModelInfo]:
        if not isinstance(payload, dict):
            raise ProviderError(
                "local runtime returned an invalid models payload",
                provider_id=self.provider_id,
            )
        if self.protocol == PROTOCOL_OLLAMA:
            items = payload.get("models")
        else:
            items = payload.get("data")
        if not isinstance(items, list):
            return []
        models: list[ModelInfo] = []
        for item in items:
            model_id = _catalog_model_id(item, ollama=self.protocol == PROTOCOL_OLLAMA)
            if model_id is None:
                continue
            source = item.get("owned_by") if isinstance(item, dict) else None
            models.append(self._model_info(model_id, source))
        return models

    def _parse_chat_message(self, payload: object) -> tuple[str, tuple[ToolCall, ...]]:
        if not isinstance(payload, dict):
            raise ProviderError(
                "local runtime returned an invalid chat payload",
                provider_id=self.provider_id,
            )
        if self.protocol == PROTOCOL_OLLAMA:
            message = payload.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                tool_calls = _ollama_tool_calls(message.get("tool_calls"), self.provider_id)
                if isinstance(content, str) and (content or tool_calls):
                    return content, tool_calls
            raise ProviderError(
                "ollama chat payload is missing message content",
                provider_id=self.provider_id,
            )
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError(
                "chat payload is missing choices",
                provider_id=self.provider_id,
            )
        first = choices[0]
        if not isinstance(first, dict):
            raise ProviderError(
                "chat payload is missing choices",
                provider_id=self.provider_id,
            )
        message = first.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"], ()
        raise ProviderError(
            "chat payload is missing message content",
            provider_id=self.provider_id,
        )

    def _parse_chat_text(self, payload: object) -> str:
        """Compatibility helper retained for text-only callers."""
        return self._parse_chat_message(payload)[0]

    async def _iter_openai_stream(
        self, response: TransportResponse
    ) -> AsyncIterator[ChatEvent]:
        for line in response.iter_lines():
            stripped = line.strip()
            if not stripped or stripped.startswith(":"):
                continue
            if not stripped.startswith("data:"):
                continue
            data = stripped[5:].strip()
            if data == "[DONE]":
                return
            try:
                payload = json.loads(data)
            except json.JSONDecodeError as exc:
                raise ProviderError(
                    "local runtime returned an invalid stream chunk",
                    provider_id=self.provider_id,
                ) from exc
            text = _openai_delta_text(payload)
            if text:
                yield ChatEvent(type="delta", text=text)

    async def _iter_ollama_stream(
        self, response: TransportResponse
    ) -> AsyncIterator[ChatEvent]:
        for line in response.iter_lines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ProviderError(
                    "local runtime returned an invalid stream chunk",
                    provider_id=self.provider_id,
                ) from exc
            if not isinstance(payload, dict):
                raise ProviderError(
                    "local runtime returned an invalid stream chunk",
                    provider_id=self.provider_id,
                )
            message = payload.get("message")
            if isinstance(message, dict):
                text = message.get("content")
                if isinstance(text, str) and text:
                    yield ChatEvent(type="delta", text=text)
            if payload.get("done") is True:
                return

    def _model_info(self, model_id: str, source: object) -> ModelInfo:
        resolved_source = source if isinstance(source, str) and source else self.provider_id
        return ModelInfo(
            provider_id=self.provider_id,
            model_id=model_id,
            display_name=model_id,
            text=True,
            streaming=True,
            local=True,
            source=resolved_source,
            license="",
        )

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: object | None = None,
        stream: bool = False,
    ) -> TransportResponse:
        assert_endpoint_allowed(
            self.base_url,
            allow_remote=self.allow_remote,
            provider_id=self.provider_id,
        )
        url = join_endpoint(self.base_url, path)
        try:
            return self._transport.request(
                method,
                url,
                headers=self._headers(),
                json_body=json_body,
                stream=stream,
                timeout=DEFAULT_TIMEOUT,
            )
        except ProviderError:
            raise
        except (OSError, TimeoutError) as exc:
            raise ProviderOfflineError(
                "local runtime is unreachable",
                provider_id=self.provider_id,
            ) from exc

    def _raise_http(self, response: TransportResponse) -> None:
        if response.status_code in {401, 403}:
            raise ProviderAuthError(
                f"local runtime rejected credentials (HTTP {response.status_code})",
                provider_id=self.provider_id,
            )
        if response.status_code >= 400:
            raise ProviderError(
                f"local runtime returned HTTP {response.status_code}",
                provider_id=self.provider_id,
            )


def _catalog_model_id(item: object, *, ollama: bool) -> str | None:
    if not isinstance(item, dict):
        return None
    if ollama:
        for key in ("name", "model"):
            value = item.get(key)
            if isinstance(value, str) and value:
                return value
        return None
    value = item.get("id")
    if isinstance(value, str) and value:
        return value
    return None


def _openai_delta_text(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    delta = first.get("delta")
    if not isinstance(delta, dict):
        return ""
    text = delta.get("content")
    return text if isinstance(text, str) else ""


def _ollama_tool_calls(value: object, provider_id: str) -> tuple[ToolCall, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ProviderError(
            "ollama chat payload has invalid tool calls", provider_id=provider_id
        )
    calls: list[ToolCall] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ProviderError(
                "ollama chat payload has invalid tool calls", provider_id=provider_id
            )
        function = item.get("function")
        if not isinstance(function, dict):
            raise ProviderError(
                "ollama chat payload has invalid tool calls", provider_id=provider_id
            )
        name = function.get("name")
        arguments = function.get("arguments")
        if not isinstance(name, str) or not name or not isinstance(arguments, dict):
            raise ProviderError(
                "ollama chat payload has invalid tool calls", provider_id=provider_id
            )
        call_id = item.get("id")
        if not isinstance(call_id, str) or not call_id:
            call_id = f"ollama-call-{index}"
        calls.append(ToolCall(id=call_id, name=name, arguments=arguments))
    return tuple(calls)
