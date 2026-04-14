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


@pytest.mark.asyncio
async def test_auth_required_on_v1_chat_completions(client_with_keys, ollama_base: str):
    with respx.mock:
        respx.post(f"{ollama_base}/api/chat").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "m",
                    "message": {"role": "assistant", "content": "x"},
                    "done": True,
                },
            )
        )
        r = await client_with_keys.post(
            "/v1/chat/completions",
            json={"model": "m", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_key_on_v1_chat_completions(client_with_keys, ollama_base: str):
    with respx.mock:
        respx.post(f"{ollama_base}/api/chat").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "m",
                    "message": {"role": "assistant", "content": "x"},
                    "done": True,
                },
            )
        )
        r = await client_with_keys.post(
            "/v1/chat/completions",
            json={"model": "m", "messages": [{"role": "user", "content": "hi"}]},
            headers={"Authorization": "Bearer wrong"},
        )
        assert r.status_code == 403
        assert r.json()["error"]["type"] == "authentication_error"


@pytest.mark.asyncio
async def test_auth_bearer_ok_chat_completions_non_stream(client_with_keys, ollama_base: str):
    with respx.mock:
        respx.post(f"{ollama_base}/api/chat").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "m",
                    "message": {"role": "assistant", "content": "ok"},
                    "done": True,
                    "prompt_eval_count": 1,
                    "eval_count": 1,
                },
            )
        )
        r = await client_with_keys.post(
            "/v1/chat/completions",
            json={"model": "m", "messages": [{"role": "user", "content": "hi"}], "stream": False},
            headers={"Authorization": "Bearer secret-key"},
        )
        assert r.status_code == 200
        assert r.json()["choices"][0]["message"]["content"] == "ok"
