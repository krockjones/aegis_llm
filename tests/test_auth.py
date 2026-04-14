from __future__ import annotations

import httpx
import pytest
import respx


@pytest.mark.asyncio
async def test_auth_required_on_v1_models(client_with_keys, ollama_base: str):
    with respx.mock:
        respx.get(f"{ollama_base}/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
        r = await client_with_keys.get("/v1/models")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_bearer_ok(client_with_keys, ollama_base: str):
    with respx.mock:
        respx.get(f"{ollama_base}/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
        r = await client_with_keys.get("/v1/models", headers={"Authorization": "Bearer secret-key"})
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_invalid_api_key_returns_403(client_with_keys, ollama_base: str):
    with respx.mock:
        respx.get(f"{ollama_base}/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
        r = await client_with_keys.get(
            "/v1/models",
            headers={"Authorization": "Bearer wrong"},
        )
        assert r.status_code == 403
        assert r.json()["error"]["type"] == "authentication_error"


@pytest.mark.asyncio
async def test_healthz_public_with_keys(client_with_keys):
    r = await client_with_keys.get("/healthz")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_auth_required_on_v1_embeddings(client_with_keys, ollama_base: str):
    with respx.mock:
        respx.post(f"{ollama_base}/api/embed").mock(
            return_value=httpx.Response(200, json={"model": "m", "embeddings": [[0.0]], "prompt_eval_count": 1})
        )
        r = await client_with_keys.post(
            "/v1/embeddings",
            json={"model": "m", "input": "x"},
        )
        assert r.status_code == 401
