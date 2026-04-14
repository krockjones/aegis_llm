"""Backend selection for the ASGI app.

Only ``ollama`` is implemented and supported in production. ``Backend`` exists so
routes and tests depend on a small protocol instead of concrete HTTP client
details. Unsupported ``AEGISLLM_BACKEND`` values fail at startup with a clear
error—this is not a plugin ecosystem or advertised multi-vendor switch.
"""

from __future__ import annotations

import httpx

from aegis_llm.backends.base import Backend
from aegis_llm.backends.ollama import OllamaBackend
from aegis_llm.config import Settings


def create_backend(settings: Settings, client: httpx.AsyncClient) -> Backend:
    """Instantiate the configured upstream adapter.

    Raises ``ValueError`` when ``settings.backend_type`` is not a supported id.
    """
    bt = settings.backend_type.strip().lower()
    if bt == "ollama":
        return OllamaBackend(settings.upstream_base_url, client)
    raise ValueError(f"Unsupported AEGISLLM_BACKEND={settings.backend_type!r} (supported: ollama)")
