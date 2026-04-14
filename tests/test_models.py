from __future__ import annotations

import httpx
import pytest
import respx


@pytest.mark.asyncio
@respx.mock
async def test_v1_models(client, ollama_base: str):
    respx.get(f"{ollama_base}/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={
                "models": [
                    {
                        "name": "llama3:latest",
                        "size": 999,
                        "digest": "sha256:abc",
                        "modified_at": "2024-01-01T00:00:00Z",
                    }
                ]
            },
        )
    )
    r = await client.get("/v1/models")
    assert r.status_code == 200
    assert r.headers.get("X-AegisLLM-Backend") == "ollama"
    assert r.headers.get("X-AegisLLM-Upstream-Base") == ollama_base
    data = r.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "llama3:latest"
    assert data["data"][0]["owned_by"] == "ollama"
    xo = data["data"][0]["x_ollama"]
    assert xo["size"] == 999
    assert xo["digest"] == "sha256:abc"
    assert xo["modified_at"] == "2024-01-01T00:00:00Z"
