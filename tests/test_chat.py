from __future__ import annotations

import httpx
import pytest
import respx


@pytest.mark.asyncio
@respx.mock
async def test_chat_completions_non_stream(client, ollama_base: str):
    respx.post(f"{ollama_base}/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "llama3",
                "message": {"role": "assistant", "content": "hello"},
                "done": True,
                "prompt_eval_count": 3,
                "eval_count": 2,
            },
        )
    )
    r = await client.post(
        "/v1/chat/completions",
        json={
            "model": "llama3",
            "messages": [{"role": "user", "content": "hi"}],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["choices"][0]["message"]["content"] == "hello"
    assert body["usage"]["prompt_tokens"] == 3
    assert body["usage"]["completion_tokens"] == 2


@pytest.mark.asyncio
@respx.mock
async def test_chat_completions_upstream_error(client, ollama_base: str):
    respx.post(f"{ollama_base}/api/chat").mock(return_value=httpx.Response(500, text="boom"))
    r = await client.post(
        "/v1/chat/completions",
        json={"model": "x", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 502
    assert r.json()["error"]["type"] == "upstream_http_error"


@pytest.mark.asyncio
async def test_chat_completions_missing_model(client):
    r = await client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["type"] == "invalid_request_error"
    assert "model" in body["error"]["message"].lower()


@pytest.mark.asyncio
async def test_chat_completions_messages_not_list(client):
    r = await client.post(
        "/v1/chat/completions",
        json={"model": "m", "messages": "nope"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["type"] == "invalid_request_error"


@pytest.mark.asyncio
@respx.mock
async def test_chat_completions_content_list_parts(client, ollama_base: str):
    respx.post(f"{ollama_base}/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "m",
                "message": {"role": "assistant", "content": "ab"},
                "done": True,
                "prompt_eval_count": 1,
                "eval_count": 1,
            },
        )
    )
    r = await client.post(
        "/v1/chat/completions",
        json={
            "model": "m",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "a"},
                        {"type": "text", "text": "b"},
                    ],
                }
            ],
        },
    )
    assert r.status_code == 200
    assert r.json()["choices"][0]["message"]["content"] == "ab"


@pytest.mark.scenario("chat-stream-sse")
@pytest.mark.asyncio
@respx.mock
async def test_chat_completions_stream(client, ollama_base: str):
    """Tier A (respx): upstream returns NDJSON chunks; Guard maps them to OpenAI-style SSE chunks and ends with ``[DONE]``.

    See ``build_log/SCENARIO_COVERAGE.md`` (SSE / NDJSON streaming) for the operator-facing mapping.
    """
    lines = [
        '{"model":"m","message":{"role":"assistant","content":"he"},"done":false}',
        '{"model":"m","message":{"role":"assistant","content":"llo"},"done":false}',
        '{"model":"m","message":{"role":"assistant","content":""},"done":true}',
    ]
    stream = httpx.ByteStream(b"\n".join(line.encode() for line in lines) + b"\n")

    respx.post(f"{ollama_base}/api/chat").mock(
        return_value=httpx.Response(200, stream=stream, headers={"content-type": "application/x-ndjson"})
    )
    r = await client.post(
        "/v1/chat/completions",
        json={"model": "m", "messages": [{"role": "user", "content": "hi"}], "stream": True},
    )
    assert r.status_code == 200
    text = r.text
    assert "chat.completion.chunk" in text
    assert "[DONE]" in text
