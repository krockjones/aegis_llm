from __future__ import annotations

import json

import httpx
import pytest
import respx


@pytest.mark.scenario("embeddings-single")
@pytest.mark.asyncio
@respx.mock
async def test_embeddings_single_string(client, ollama_base: str):
    respx.post(f"{ollama_base}/api/embed").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "all-minilm",
                "embeddings": [[0.1, 0.2, 0.3]],
                "prompt_eval_count": 4,
            },
        )
    )
    r = await client.post(
        "/v1/embeddings",
        json={"model": "all-minilm", "input": "hello world"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "list"
    assert len(body["data"]) == 1
    assert body["data"][0]["object"] == "embedding"
    assert body["data"][0]["index"] == 0
    assert body["data"][0]["embedding"] == [0.1, 0.2, 0.3]
    assert body["usage"]["prompt_tokens"] == 4
    assert r.headers.get("X-AegisLLM-Backend") == "ollama"


@pytest.mark.asyncio
@respx.mock
async def test_embeddings_batch(client, ollama_base: str):
    respx.post(f"{ollama_base}/api/embed").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "m",
                "embeddings": [[1.0], [2.0]],
                "prompt_eval_count": 10,
            },
        )
    )
    r = await client.post(
        "/v1/embeddings",
        json={"model": "m", "input": ["a", "b"]},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 2
    assert data[0]["index"] == 0
    assert data[1]["index"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_embeddings_upstream_error(client, ollama_base: str):
    respx.post(f"{ollama_base}/api/embed").mock(return_value=httpx.Response(500, text="no"))
    r = await client.post(
        "/v1/embeddings",
        json={"model": "m", "input": "x"},
    )
    assert r.status_code == 502
    assert r.json()["error"]["type"] == "upstream_http_error"


@pytest.mark.asyncio
@respx.mock
async def test_embeddings_upstream_timeout(client, ollama_base: str):
    respx.post(f"{ollama_base}/api/embed").mock(side_effect=httpx.ReadTimeout("t"))
    r = await client.post(
        "/v1/embeddings",
        json={"model": "m", "input": "x"},
    )
    assert r.status_code == 504


@pytest.mark.asyncio
async def test_embeddings_rejects_unknown_top_level_key(client):
    r = await client.post(
        "/v1/embeddings",
        json={"model": "m", "input": "hello", "user": "x"},
    )
    assert r.status_code == 400
    err = r.json()["error"]
    assert err["type"] == "invalid_request_error"
    msg = err["message"].lower()
    assert "extra" in msg or "user" in msg


@pytest.mark.asyncio
async def test_embeddings_empty_input_rejected(client):
    r = await client.post(
        "/v1/embeddings",
        json={"model": "m", "input": ""},
    )
    assert r.status_code == 400
    assert r.json()["error"]["type"] == "invalid_request_error"


@pytest.mark.asyncio
async def test_embeddings_rejects_base64_encoding(client):
    r = await client.post(
        "/v1/embeddings",
        json={"model": "m", "input": "hello", "encoding_format": "base64"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["type"] == "invalid_request_error"


@pytest.mark.asyncio
@respx.mock
async def test_embeddings_passes_dimensions(client, ollama_base: str):
    route = respx.post(f"{ollama_base}/api/embed").mock(
        return_value=httpx.Response(200, json={"model": "m", "embeddings": [[0.0]], "prompt_eval_count": 1})
    )
    r = await client.post(
        "/v1/embeddings",
        json={"model": "m", "input": "hi", "dimensions": 256},
    )
    assert r.status_code == 200
    assert route.calls.last.request.content
    sent = json.loads(route.calls.last.request.content)
    assert sent.get("dimensions") == 256
