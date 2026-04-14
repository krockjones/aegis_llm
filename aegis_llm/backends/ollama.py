from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncIterator

import httpx

from aegis_llm.logging_setup import get_logger

_log = get_logger("ollama")


def _response_json(r: httpx.Response) -> Any:
    try:
        return r.json()
    except json.JSONDecodeError:
        raise ValueError("Upstream returned invalid JSON") from None


class OllamaBackend:
    name = "ollama"

    def __init__(self, base_url: str, client: httpx.AsyncClient) -> None:
        self._client = client
        self._base = base_url.rstrip("/")

    async def health_probe(self) -> tuple[bool, str | None]:
        try:
            r = await self._client.get(f"{self._base}/api/tags")
            if r.status_code == 200:
                return True, None
            return False, f"ollama returned HTTP {r.status_code}"
        except httpx.ConnectError as e:
            return False, f"connect_error: {e}"
        except httpx.TimeoutException as e:
            return False, f"timeout: {e}"
        except OSError as e:
            return False, f"os_error: {e}"

    async def list_models(self) -> list[dict[str, Any]]:
        r = await self._client.get(f"{self._base}/api/tags")
        r.raise_for_status()
        data = _response_json(r)
        models = data.get("models") or []
        out: list[dict[str, Any]] = []
        for m in models:
            if not isinstance(m, dict):
                continue
            name = m.get("name")
            if not name:
                continue
            entry: dict[str, Any] = {
                "id": str(name),
                "object": "model",
                "created": 0,
                "owned_by": "ollama",
            }
            ollama_meta: dict[str, Any] = {}
            for key in ("size", "digest", "modified_at", "details"):
                if key in m and m[key] is not None:
                    ollama_meta[key] = m[key]
            if ollama_meta:
                entry["x_ollama"] = ollama_meta
            out.append(entry)
        return out

    def _openai_messages_to_ollama(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content")
            if isinstance(content, list):
                text_parts: list[str] = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(str(part.get("text", "")))
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = "".join(text_parts)
            elif content is None:
                content = ""
            else:
                content = str(content)
            out.append({"role": role, "content": content})
        return out

    def _build_ollama_chat_body(self, payload: dict[str, Any]) -> dict[str, Any]:
        model = payload.get("model")
        if not model:
            raise ValueError("model is required")
        messages = payload.get("messages") or []
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
        stream = bool(payload.get("stream", False))
        ollama_messages = self._openai_messages_to_ollama(messages)
        options: dict[str, Any] = {}
        if "temperature" in payload and payload["temperature"] is not None:
            options["temperature"] = float(payload["temperature"])
        if "top_p" in payload and payload["top_p"] is not None:
            options["top_p"] = float(payload["top_p"])
        if "max_tokens" in payload and payload["max_tokens"] is not None:
            options["num_predict"] = int(payload["max_tokens"])
        if "stop" in payload and payload["stop"] is not None:
            stop = payload["stop"]
            if isinstance(stop, str):
                options["stop"] = [stop]
            elif isinstance(stop, list):
                options["stop"] = stop
        body: dict[str, Any] = {
            "model": str(model),
            "messages": ollama_messages,
            "stream": stream,
        }
        if options:
            body["options"] = options
        return body

    def _to_openai_completion(self, ollama_resp: dict[str, Any], model: str) -> dict[str, Any]:
        msg = ollama_resp.get("message") or {}
        content = msg.get("content") or ""
        prompt_tokens = int(ollama_resp.get("prompt_eval_count") or 0)
        completion_tokens = int(ollama_resp.get("eval_count") or 0)
        cid = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())
        return {
            "id": cid,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = self._build_ollama_chat_body({**payload, "stream": False})
        r = await self._client.post(f"{self._base}/api/chat", json=body)
        r.raise_for_status()
        data = _response_json(r)
        model = str(payload.get("model") or body["model"])
        return self._to_openai_completion(data, model)

    async def chat_completion_stream(self, payload: dict[str, Any]) -> AsyncIterator[bytes]:
        body = self._build_ollama_chat_body({**payload, "stream": True})
        cid = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())
        model = str(payload.get("model") or body["model"])

        async with self._client.stream("POST", f"{self._base}/api/chat", json=body) as r:
            r.raise_for_status()
            first = True
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    _log.debug("skipped_malformed_ndjson_line line_preview=%r", line[:200])
                    continue
                msg = chunk.get("message") or {}
                piece = msg.get("content") or ""
                done = bool(chunk.get("done"))
                delta: dict[str, Any] = {}
                if first:
                    delta["role"] = "assistant"
                    first = False
                if piece:
                    delta["content"] = piece
                finish = "stop" if done else None
                if not delta and finish is None:
                    continue
                openai_chunk = {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
                }
                yield f"data: {json.dumps(openai_chunk)}\n\n".encode()
                if done:
                    break
            yield b"data: [DONE]\n\n"

    async def embeddings(self, ollama_body: dict[str, Any]) -> dict[str, Any]:
        """Map Ollama POST /api/embed response to OpenAI-style POST /v1/embeddings."""
        r = await self._client.post(f"{self._base}/api/embed", json=ollama_body)
        r.raise_for_status()
        data = _response_json(r)
        raw = data.get("embeddings") or []
        out_rows: list[dict[str, Any]] = []
        for i, emb in enumerate(raw):
            if not isinstance(emb, list):
                continue
            out_rows.append(
                {
                    "object": "embedding",
                    "embedding": emb,
                    "index": i,
                }
            )
        model_name = str(data.get("model") or ollama_body.get("model", ""))
        prompt_tokens = int(data.get("prompt_eval_count") or 0)
        return {
            "object": "list",
            "data": out_rows,
            "model": model_name,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "total_tokens": prompt_tokens,
            },
        }
