from __future__ import annotations

import httpx
import pytest
import respx


@pytest.mark.scenario("openai-models-shape")
@pytest.mark.asyncio
@respx.mock
async def test_v1_models_openai_client_shape(client, ollama_base: str):
    """Fields commonly assumed by OpenAI-shaped clients (e.g. chat UIs)."""
    respx.get(f"{ollama_base}/api/tags").mock(
        return_value=httpx.Response(200, json={"models": [{"name": "m1"}]}),
    )
    r = await client.get("/v1/models")
    assert r.status_code == 200
    assert r.headers.get("X-AegisLLM-Upstream-Base") == ollama_base
    payload = r.json()
    assert payload.get("object") == "list"
    assert isinstance(payload.get("data"), list)
    assert len(payload["data"]) >= 1
    row = payload["data"][0]
    for key in ("id", "object", "owned_by"):
        assert key in row, f"missing {key}"
    assert row["object"] == "model"
