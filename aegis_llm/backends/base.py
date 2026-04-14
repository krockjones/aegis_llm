from __future__ import annotations

from typing import Any, AsyncIterator, Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    """Contract for upstream adapters. Today only `ollama` is implemented."""

    name: str

    async def health_probe(self) -> tuple[bool, str | None]:
        """Upstream readiness for ``/readyz``; semantics are adapter-specific."""

        ...

    async def list_models(self) -> list[dict[str, Any]]: ...

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    async def chat_completion_stream(self, payload: dict[str, Any]) -> AsyncIterator[bytes]: ...

    async def embeddings(self, payload: dict[str, Any]) -> dict[str, Any]: ...
