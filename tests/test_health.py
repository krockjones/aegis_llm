from __future__ import annotations

import httpx
import pytest
import respx


@pytest.mark.asyncio
async def test_healthz(client):
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
@respx.mock
async def test_readyz_ok(client, ollama_base: str):
    respx.get(f"{ollama_base}/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
    r = await client.get("/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["backend"] == "ollama"


@pytest.mark.asyncio
@respx.mock
async def test_readyz_fail(client, ollama_base: str):
    respx.get(f"{ollama_base}/api/tags").mock(return_value=httpx.Response(503, text="no"))
    r = await client.get("/readyz")
    assert r.status_code == 503
    assert r.json()["status"] == "not_ready"
