from __future__ import annotations

import httpx
import pytest
import respx

from aegis_llm.backends.factory import create_backend
from aegis_llm.config import Settings, SettingsError, load_settings


@pytest.mark.asyncio
@respx.mock
async def test_v1_models_upstream_timeout(client, ollama_base: str):
    respx.get(f"{ollama_base}/api/tags").mock(side_effect=httpx.ReadTimeout("timeout"))
    r = await client.get("/v1/models")
    assert r.status_code == 504
    assert r.json()["error"]["type"] == "timeout"


@pytest.mark.asyncio
@respx.mock
async def test_v1_models_upstream_connect_error(client, ollama_base: str):
    respx.get(f"{ollama_base}/api/tags").mock(side_effect=httpx.ConnectError("refused"))
    r = await client.get("/v1/models")
    assert r.status_code == 502
    assert r.json()["error"]["type"] == "connection_error"


@pytest.mark.scenario("chat-stream-sse-error")
@pytest.mark.asyncio
@respx.mock
async def test_chat_stream_upstream_http_error(client, ollama_base: str):
    """Tier A (respx): upstream HTTP error while ``stream: true`` still yields SSE (error payload + ``[DONE]``)."""
    respx.post(f"{ollama_base}/api/chat").mock(return_value=httpx.Response(500, text="fail"))
    r = await client.post(
        "/v1/chat/completions",
        json={"model": "m", "messages": [{"role": "user", "content": "hi"}], "stream": True},
    )
    assert r.status_code == 200
    assert "upstream_http_error" in r.text
    assert r.text.count("[DONE]") >= 1


@pytest.mark.asyncio
async def test_x_request_id_roundtrip(client):
    r = await client.get("/healthz", headers={"X-Request-Id": "abc-123"})
    assert r.status_code == 200
    assert r.headers.get("x-request-id") == "abc-123"


@pytest.mark.asyncio
async def test_auth_malformed_bearer(client_with_keys):
    r = await client_with_keys.get("/v1/models", headers={"Authorization": "NotBearer x"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_bearer_without_token(client_with_keys):
    r = await client_with_keys.get("/v1/models", headers={"Authorization": "Bearer"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_backend_rejects_unknown_type():
    s = Settings(
        backend_type="vllm-not-implemented",
        upstream_base_url="http://localhost:8000",
        listen_host="127.0.0.1",
        listen_port=8765,
        api_keys=(),
        connect_timeout=1.0,
        read_timeout=2.0,
        log_level="INFO",
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match="Unsupported"):
            create_backend(s, client)


@pytest.mark.asyncio
@respx.mock
async def test_readyz_upstream_timeout(client, ollama_base: str):
    respx.get(f"{ollama_base}/api/tags").mock(side_effect=httpx.ReadTimeout("timeout"))
    r = await client.get("/readyz")
    assert r.status_code == 503


@pytest.mark.asyncio
@respx.mock
async def test_readyz_ok_when_upstream_tags_succeeds(client, ollama_base: str):
    respx.get(f"{ollama_base}/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
    r = await client.get("/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["backend"] == "ollama"


@pytest.mark.asyncio
@respx.mock
async def test_v1_models_invalid_json_body_returns_502(client, ollama_base: str):
    respx.get(f"{ollama_base}/api/tags").mock(return_value=httpx.Response(200, text="not json"))
    r = await client.get("/v1/models")
    assert r.status_code == 502
    assert r.json()["error"]["type"] == "upstream_error"


def test_load_settings_rejects_bad_upstream_scheme(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AEGISLLM_CONFIG", raising=False)
    monkeypatch.setenv("AEGISLLM_UPSTREAM_BASE_URL", "ftp://x")
    with pytest.raises(SettingsError, match="http:// or https://"):
        load_settings()
