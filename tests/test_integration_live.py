from __future__ import annotations

import os

import httpx
import pytest

pytestmark = pytest.mark.integration


def _live_guard_headers() -> dict[str, str]:
    bearer = os.environ.get("AEGISLLM_LIVE_BEARER")
    if bearer and bearer.strip():
        return {"Authorization": f"Bearer {bearer.strip()}"}
    return {}


@pytest.mark.asyncio
async def test_live_ollama_tags_reachable() -> None:
    """Opt-in: verify real Ollama /api/tags matches what the gateway assumes (drift guard).

    Set AEGISLLM_LIVE_OLLAMA=1 and optionally AEGISLLM_UPSTREAM_BASE_URL (default http://127.0.0.1:11434).
    """
    if os.environ.get("AEGISLLM_LIVE_OLLAMA") != "1":
        pytest.skip("Set AEGISLLM_LIVE_OLLAMA=1 to run live Ollama integration checks")

    base = os.environ.get("AEGISLLM_UPSTREAM_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{base}/api/tags")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "models" in data


@pytest.mark.asyncio
async def test_live_guard_readyz_and_v1_models_headers() -> None:
    """Opt-in: hit running Guard (not ASGI-mocked) for /readyz and /v1/models disclosure headers.

    Requires ``AEGISLLM_LIVE_OLLAMA=1``. Set ``AEGISLLM_GUARD_BASE_URL`` if Guard is not at
    ``http://127.0.0.1:8765``. Start Guard separately (e.g. ``aegis-llm`` or ``docker compose``).

    Skips if Guard is not listening, or if /readyz is 503 (upstream Ollama not reachable from Guard).

    When Guard uses API keys, set ``AEGISLLM_LIVE_BEARER`` to the same token used for ``/v1/*``.
    """
    if os.environ.get("AEGISLLM_LIVE_OLLAMA") != "1":
        pytest.skip("Set AEGISLLM_LIVE_OLLAMA=1 to run live Guard integration checks")

    guard = os.environ.get("AEGISLLM_GUARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    headers = _live_guard_headers()
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            hz = await client.get(f"{guard}/healthz")
        except httpx.ConnectError:
            pytest.skip(
                f"Guard not reachable at {guard}; start it (e.g. `aegis-llm` or `docker compose up`) "
                "or set AEGISLLM_GUARD_BASE_URL."
            )
        assert hz.status_code == 200, hz.text

        rz = await client.get(f"{guard}/readyz")
        if rz.status_code == 503:
            pytest.skip(
                "Guard /readyz returned 503 (upstream not ready). "
                "Ensure Ollama is reachable from Guard (same host URL as configured upstream)."
            )
        assert rz.status_code == 200, rz.text

        m = await client.get(f"{guard}/v1/models", headers=headers)
    assert m.status_code == 200, m.text
    assert m.headers.get("X-AegisLLM-Backend") == "ollama"
    upstream = m.headers.get("X-AegisLLM-Upstream-Base")
    assert upstream, "expected X-AegisLLM-Upstream-Base on GET /v1/models"
    assert upstream.startswith("http://") or upstream.startswith("https://")


@pytest.mark.asyncio
async def test_live_guard_chat_completion_stream() -> None:
    """Opt-in: real Guard→Ollama SSE for ``POST /v1/chat/completions`` with ``stream: true``.

    Requires ``AEGISLLM_LIVE_OLLAMA=1``. Uses ``AEGISLLM_GUARD_BASE_URL`` (default
    ``http://127.0.0.1:8765``). Picks ``data[0]["id"]`` from ``GET /v1/models`` (no
    hard-coded model name).

    Skips when Guard is unreachable, ``/readyz`` is 503, the models list is empty, or
    ``GET /v1/models`` returns 401/403 — set ``AEGISLLM_LIVE_BEARER`` to the configured
    API key token (same as ``AEGISLLM_API_KEYS`` on Guard).
    """
    if os.environ.get("AEGISLLM_LIVE_OLLAMA") != "1":
        pytest.skip("Set AEGISLLM_LIVE_OLLAMA=1 to run live Guard integration checks")

    guard = os.environ.get("AEGISLLM_GUARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    headers = _live_guard_headers()
    timeout = httpx.Timeout(30.0, read=180.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            hz = await client.get(f"{guard}/healthz")
        except httpx.ConnectError:
            pytest.skip(
                f"Guard not reachable at {guard}; start it (e.g. `aegis-llm` or `docker compose up`) "
                "or set AEGISLLM_GUARD_BASE_URL."
            )
        assert hz.status_code == 200, hz.text

        rz = await client.get(f"{guard}/readyz")
        if rz.status_code == 503:
            pytest.skip(
                "Guard /readyz returned 503 (upstream not ready). "
                "Ensure Ollama is reachable from Guard (same host URL as configured upstream)."
            )
        assert rz.status_code == 200, rz.text

        m = await client.get(f"{guard}/v1/models", headers=headers)
        if m.status_code in (401, 403):
            pytest.skip(
                "GET /v1/models returned HTTP "
                f"{m.status_code}; set AEGISLLM_LIVE_BEARER when API keys are configured on Guard."
            )
        assert m.status_code == 200, m.text
        payload = m.json()
        models = payload.get("data") or []
        if not models:
            pytest.skip("GET /v1/models returned no models (empty data); load a model in Ollama.")

        model_id = models[0]["id"]

        async with client.stream(
            "POST",
            f"{guard}/v1/chat/completions",
            headers=headers,
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "Say hi in a few words."}],
                "stream": True,
            },
        ) as stream_resp:
            assert stream_resp.status_code == 200, (await stream_resp.aread()).decode()
            content_type = stream_resp.headers.get("content-type")
            if content_type:
                assert "event-stream" in content_type.lower()
            raw = await stream_resp.aread()

    text = raw.decode(errors="replace")
    assert "chat.completion.chunk" in text
    assert "[DONE]" in text


@pytest.mark.asyncio
async def test_live_guard_embeddings_roundtrip() -> None:
    """Opt-in: ``POST /v1/embeddings`` through a running Guard to real Ollama.

    Requires ``AEGISLLM_LIVE_OLLAMA=1`` and a reachable Guard (``AEGISLLM_GUARD_BASE_URL``).
    Set ``AEGISLLM_LIVE_EMBED_MODEL`` to an Ollama model you have pulled (default
    ``nomic-embed-text``). When Guard uses ``AEGISLLM_API_KEYS``, set ``AEGISLLM_LIVE_BEARER``
    to the same token for ``Authorization``.

    Skips on connect errors, ``/readyz`` 503, 401/403 on embeddings (auth), or 502 when the
    model is missing upstream.
    """
    if os.environ.get("AEGISLLM_LIVE_OLLAMA") != "1":
        pytest.skip("Set AEGISLLM_LIVE_OLLAMA=1 to run live Guard integration checks")

    guard = os.environ.get("AEGISLLM_GUARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    model = os.environ.get("AEGISLLM_LIVE_EMBED_MODEL", "nomic-embed-text").strip()
    headers = _live_guard_headers()

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=120.0)) as client:
        try:
            hz = await client.get(f"{guard}/healthz")
        except httpx.ConnectError:
            pytest.skip(
                f"Guard not reachable at {guard}; start it or set AEGISLLM_GUARD_BASE_URL."
            )
        assert hz.status_code == 200, hz.text

        rz = await client.get(f"{guard}/readyz")
        if rz.status_code == 503:
            pytest.skip("Guard /readyz returned 503 (upstream not ready).")

        r = await client.post(
            f"{guard}/v1/embeddings",
            headers=headers,
            json={"model": model, "input": "alpha live embed smoke"},
        )
        if r.status_code in (401, 403):
            pytest.skip(
                f"POST /v1/embeddings returned HTTP {r.status_code}; "
                "set AEGISLLM_LIVE_BEARER when Guard is configured with API keys."
            )
        if r.status_code == 502:
            pytest.skip(
                f"Embeddings upstream error (HTTP 502); ensure model {model!r} is pulled in Ollama."
            )
        assert r.status_code == 200, r.text

    data = r.json()
    assert data.get("object") == "list"
    rows = data.get("data") or []
    assert len(rows) >= 1
    emb = rows[0].get("embedding")
    assert isinstance(emb, list)
    assert len(emb) >= 1
    assert all(isinstance(x, (int, float)) for x in emb)
