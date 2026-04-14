# AegisLLM Guard — API contract (canonical subset)

**Package version:** `0.2.0` (see `aegis_llm.version.__version__`).  
This file is the **canonical statement** of what integrators may rely on. Behavior not described here should not be relied upon.

---

## Compatibility philosophy (interpretation)

- This document defines the **supported subset** of OpenAI-**shaped** HTTP usage in front of **Ollama**.
- Generated **OpenAPI** at `/docs` and `/openapi.json` is **descriptive** (what the server exposes and validates today). It is **not** a promise of full OpenAI API parity.
- **Undocumented behavior** (extra response fields, ordering, future headers) may change; do not depend on it without checking this file and tests.
- Request fields may be **rejected** (4xx validation), **ignored** (silent drop), or **accepted with mediated semantics** (forwarded or transformed as tables below state). Those are different outcomes; “parses OK” does not mean “affects upstream.”
- **Production backend support today is Ollama only.** Other `AEGISLLM_BACKEND` values are not supported.

---

## Purpose

AegisLLM Guard is a narrow **reliability gateway**: timeouts, health, optional auth, typed validation for implemented routes, and consistent error shapes. When this file and implementation diverge, treat **`aegis_llm` source** as truth until the contract is updated intentionally.

**Code truth baseline:** `aegis_llm/schemas.py`, `aegis_llm/routes/openai.py`, `aegis_llm/routes/health.py`, `aegis_llm/backends/ollama.py`, `aegis_llm/errors.py`, `aegis_llm/middleware/auth.py`.

---

## Backends (production reality)

| Backend id (`AEGISLLM_BACKEND`) | Status |
|-----------------------------------|--------|
| `ollama` | **Supported.** After request validation, traffic to `/v1/*` is forwarded to the configured Ollama HTTP API. |
| Any other value | **Unsupported** — startup/backend creation fails with a clear error. |

The **factory** and `Backend` abstraction exist for structure, tests, and future backends. They are **not** a multi-backend product claim.

---

## HTTP surface

| Method | Path | Auth (if `AEGISLLM_API_KEYS` set) | Notes |
|--------|------|-------------------------------------|--------|
| `GET` | `/` | No | Service metadata JSON (`service`, `product`, `version`, `positioning`). |
| `GET` | `/healthz` | No | Liveness: process up. |
| `GET` | `/readyz` | No | Readiness: upstream probe; **503** if not ready. |
| `GET` | `/docs`, `/redoc`, `/openapi.json` | No | Interactive / generated API docs. |
| `GET` | `/v1/models` | Yes | OpenAI-style model list. |
| `POST` | `/v1/chat/completions` | Yes | Chat completions, stream or non-stream. |
| `POST` | `/v1/embeddings` | Yes | Embeddings (Ollama `POST /api/embed`). |

**Public when keys are set:** `/`, `/healthz`, `/readyz`, `/docs`, `/redoc`, `/openapi.json` — see README *Security / deployment* and [SECURITY_POSTURE.md](./SECURITY_POSTURE.md) (risks, mitigations, startup WARNING logs).

**Response headers (selected):**  
`GET /v1/models` may set `X-AegisLLM-Backend`, `X-AegisLLM-Upstream-Base` (disclosure of configured upstream). Non-stream `POST /v1/chat/completions` and `POST /v1/embeddings` may set `X-AegisLLM-Backend`. **Streaming** `POST /v1/chat/completions` does **not** set that header today (asymmetric vs non-stream).

---

## `GET /v1/models`

**Upstream:** `GET {upstream}/api/tags`.

**Success:** `200` JSON `{ "object": "list", "data": [ ... ] }`. Each item includes at minimum `id`, `object` (`model`), `created`, `owned_by`. Optional **`x_ollama`** (when Ollama supplies metadata): may include `size`, `digest`, `modified_at`, `details` — **informational only**, not a portability guarantee.

**Errors:** Transport/timeouts, connection failures, upstream HTTP errors, non-JSON success body, and OS-level errors map to **502** / **504** with unified error JSON (see *Errors*). Malformed upstream JSON yields **502** with `error.type` **`upstream_error`**.

---

## `POST /v1/chat/completions`

Validated by `ChatCompletionRequest` / `ChatMessage` in `schemas.py` (`extra="ignore"` on both: unknown keys are **ignored**, not forwarded).

### Request fields (top-level)

| Field | Request handling | Upstream / effect |
|-------|------------------|-------------------|
| `model` | **Required**; validated non-empty string | Forwarded to Ollama `model`. |
| `messages` | **Required**; non-empty list of messages | Transformed (see *Normalization*). |
| `stream` | Optional; default `false` | Forwarded; selects streaming vs single JSON response. |
| `temperature` | Optional | If present, forwarded in Ollama `options.temperature`. |
| `top_p` | Optional | If present, forwarded in Ollama `options.top_p`. |
| `max_tokens` | Optional; integer ≥ 1 if set | Mapped to Ollama `options.num_predict`. |
| `stop` | Optional string or list of strings | Mapped to Ollama `options.stop` (string wrapped as single-element list). |
| Any other top-level JSON key | **Ignored** (not an error) | Not forwarded. |

Ollama may still ignore or interpret options per its own rules; Guard forwards as documented above.

### Message objects (`messages[]`)

| Field | Request handling | Upstream / effect |
|-------|------------------|-------------------|
| `role` | **Required** (min length 1) | Forwarded (after normalization). |
| `content` | Optional `string`, `null`, or list of parts | See *Normalization*. |
| Any other key | **Ignored** | Not forwarded (e.g. `tool_calls`, `function_call` dropped). |

**Part list `content`:** Each element may be a **string** (concatenated as text) or a **dict** with `type == "text"` (uses `text` field, else empty). Other dict shapes are **skipped** (no error). Result is a single Ollama **string** `content` per message.

### Normalization / translation notes (chat)

- **Transformed:** Multi-part / list `content` → concatenated plain text for Ollama. `max_tokens` → `num_predict`. `stop` string → `stop` array in Ollama options.
- **Approximated (response):** Non-stream completion always exposes `finish_reason: "stop"` on the single choice regardless of upstream nuance. `usage` token counts come from Ollama fields `prompt_eval_count` / `eval_count` when present (else 0). Streaming chunks use OpenAI-shaped `delta` and may omit `content` on some chunks; final `finish_reason` is `stop` when Ollama signals done.
- **Passthrough-shaped:** Model name, message roles, and text content after flattening follow Ollama’s chat API expectations.

### Streaming (SSE)

- **Media type:** `text/event-stream`.
- **Frames:** `data: {json}\n\n` per chunk; stream ends with `data: [DONE]\n\n`.
- **Errors during stream:** An error may be emitted as an SSE `data:` line with an OpenAI-style `error` object, followed by `[DONE]` (see `aegis_llm.errors.sse_error_termination` and the streaming branch of `aegis_llm.routes.openai.chat_completions`). Types emitted on that path include `timeout`, `connection_error`, `upstream_http_error`, `invalid_request_error`, `upstream_error`.

#### Operational verification

End-to-end streaming validation (§1-style checklist and §1.1 provenance) is **authoritative** in `docs/INTEGRATION_OPEN_WEBUI.md` under **Streaming verification (Iteration 3)**. **Automated** real-stack SSE checks live in **`tests/test_integration_live.py`** (opt-in with `AEGISLLM_LIVE_OLLAMA=1`; see test docstrings for env vars and provenance). **Temporal status** for manual rows is recorded in the integration doc; readers must not infer manual UI status from this contract alone.

#### Known limitations (streaming)

- **Third-party variance and scope:** UIs and HTTP/SSE stacks differ (buffering, error presentation, hangs); until the integration checklist is completed and §1.1 provenance is filled for a given client, those behaviors are **not** certified here—this contract describes **only** server-side SSE framing and `sse_error_termination` semantics.

### Non-stream

- **Success:** `200` JSON `chat.completion` shape with one choice.
- **Validation:** Unknown/bad body → **400**, `error.type` **`invalid_request_error`** (unless upstream JSON parse failure → **502** `upstream_error`).

### Not supported here (see *Out of scope*)

Tools, functions, `n` > 1, logprobs, modalities beyond text flattening, system vs user semantics beyond string passthrough, Responses API.

---

## `POST /v1/embeddings`

Validated by `EmbeddingsRequest` in `schemas.py` (`extra="forbid"`: unknown **top-level** keys are **rejected**, not ignored—same validation outcome as other body errors: **400** with `error.type` **`invalid_request_error`**; see *Errors*).

### Request fields

| Field | Request handling | Upstream / effect |
|-------|------------------|-------------------|
| `model` | **Required**; non-empty string | Forwarded. |
| `input` | **Required**; non-empty string or non-empty list of non-empty strings | Forwarded as string or array in Ollama body. Empty list or empty strings → **400** validation. |
| `encoding_format` | Omitted or **`float` only** | Any other value (e.g. `base64`) → **400** (schema rejection). **Not** sent in the Ollama request body—validated only for OpenAI client compatibility (`schemas.py` `to_ollama_body`). |
| `dimensions` | Optional; integer ≥ 1 | Forwarded when set. |
| `truncate` | Optional bool | Forwarded when set. |
| Any other top-level JSON key | **Rejected** | **400**, `error.type` **`invalid_request_error`** (not forwarded). |

**Upstream:** `POST {upstream}/api/embed` with JSON body `{ model, input, ... }`.

### Normalization / translation notes (embeddings)

- **Transformed:** OpenAI-style `input` is passed through to Ollama’s expected shape (string or array).
- **Response:** OpenAI-style `{ object, data[], model, usage }`. Each `data[i]` has `object`, `embedding`, `index`. Rows with non-list embeddings from upstream may be **skipped**. `usage.prompt_tokens` / `total_tokens` derive from Ollama `prompt_eval_count` when present.

### Errors

Validation → **400**. Upstream/transport/invalid JSON → **502** / **504** as for other routes.

---

## Health

| Route | Success | Failure |
|-------|---------|---------|
| `GET /healthz` | `200` `{"status":"ok"}` | — |
| `GET /readyz` | `200` `{"status":"ready","backend":"ollama"}` | `503` `{"status":"not_ready","backend",...,"detail"}` |

Readiness uses the backend health probe (Ollama: `GET /api/tags` returns **200**).

---

## Errors

**Client JSON shape (subset):** `{ "error": { "message": string, "type": string, "code"?: string, "param"?: string } }`. Not every field appears on every error.

**Operator-oriented categories** (same payload shape; category is for reasoning, not a separate field):

| Category | Typical situation | HTTP | `error.type` (examples) |
|----------|-------------------|------|-------------------------|
| **Transport** | Upstream timeout, connection failure | 504, 502 | `timeout`, `connection_error` |
| **Validation** | Pydantic body / field validation | 400 | `invalid_request_error` |
| **Auth** | Missing/invalid Bearer, wrong API key | 401, 403 | `authentication_error` |
| **Upstream protocol / semantics** | Upstream HTTP error, non-JSON body, stream failure, `OSError` | 502 (or SSE error event) | `upstream_http_error`, `upstream_error`, etc. |

Upstream HTTP failures return a **generic** message to the client (status code only); details may be logged server-side. See `aegis_llm/errors.py`.

---

## Out of scope

### Unimplemented OpenAI API families

Examples: **Images**, **Audio**, **Assistants**, **Threads**, **Runs**, **Batch**, **Fine-tuning**, **Files** (as OpenAI API), **Moderations**, **Realtime** — any route not listed in *HTTP surface* is unsupported.

### Unimplemented or non-portable chat semantics

**Tool** / **function** calling, parallel completions (`n` > 1), **logprobs**, structured **JSON mode** guarantees, **vision** / **image** parts (non-`text` multimodal parts are not mapped), **Responses** API, and other OpenAI features not named in the chat field tables above.

### Unsupported product / backend claims

**Multi-backend routing**, quotas, billing, LiteLLM-style provider matrix, and “drop-in full OpenAI parity” are **out of scope** for this package version. Only **Ollama** behind a single configured base URL is supported.

---

## Versioning and review

Breaking behavioral changes should update this file and package version together.

---

*Last reviewed against **aegis-llm 0.2.0** — 2026-04-09.*
