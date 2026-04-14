# Iteration 04A — Schema and `extra` policy audit

**Scope:** `aegis_llm/schemas.py`, `aegis_llm/routes/openai.py`, `aegis_llm/app.py`, `docs/API_CONTRACT.md` (chat + embeddings), `tests/`, `scripts/`.  
**Date:** 2026-04-13.

---

## Executive summary

- **All request `BaseModel`s live in one file** (`schemas.py`): three models; **`EmbeddingsRequest` uses `extra="forbid"`**; **`ChatMessage` / `ChatCompletionRequest` use `extra="ignore"`**; no other package-local `BaseModel` / `ConfigDict` for HTTP bodies.
- **`RequestValidationError` is customized** in `create_app()` (`app.py`): **400** + `error_payload(..., "invalid_request_error")` with a semicolon-joined summary of Pydantic `loc` + `msg`. `main.py` only boots uvicorn; it does not register handlers.
- **Repo tests and smoke scripts do not send undocumented top-level JSON keys** on `POST /v1/chat/completions` or `POST /v1/embeddings` (no `tools`, `user`, `frequency_penalty`, etc. in fixtures); multipart `content[]` objects use `type` / `text` inside `list[dict[str, Any]]`, which is outside per-dict `forbid` until those become typed models.
- **`API_CONTRACT.md` currently promises silent ignore** for unknown chat and embeddings keys; flipping any model to `extra="forbid"` is a **documented contract change** for that route (ignored → rejected), not just an implementation detail.
- **Recommended first tighten:** `EmbeddingsRequest` → `extra="forbid"` (**risk: low** for in-repo CI; **medium** for arbitrary OpenAI clients that still send optional metadata such as `user`). Defer chat top-level forbid until real payloads (e.g. Open WebUI / SDK captures) are classified.

---

## Models and `extra` policy

| Model | File | `extra` | Declared fields (top level) | Notes |
|-------|------|---------|-----------------------------|--------|
| `ChatMessage` | `schemas.py` | `ignore` | `role`, `content` | `content`: `str \| list[dict[str, Any]] \| None` — inner dict keys are not a nested `BaseModel`; `forbid` on `ChatMessage` does not validate keys inside each part dict. |
| `ChatCompletionRequest` | `schemas.py` | `ignore` | `model`, `messages`, `stream`, `temperature`, `top_p`, `max_tokens`, `stop` | `to_backend_payload()` only forwards the supported subset. |
| `EmbeddingsRequest` | `schemas.py` | **`forbid`** (was `ignore` at audit time) | `model`, `input`, `encoding_format`, `dimensions`, `truncate` | `encoding_format` restricted to `Literal["float"] \| None`; `to_ollama_body()` omits it. Validator on `input` enforces non-empty strings. |

No additional Pydantic body models were found under `aegis_llm/routes/` (`health.py` has no JSON body).

---

## FastAPI validation error path

| Location | Behavior |
|----------|----------|
| `aegis_llm/app.py` (`create_app`) | `@app.exception_handler(RequestValidationError)` → **400**, body from `error_payload(message, "invalid_request_error")`, message built from `exc.errors()` (`loc` sans `"body"`, joined with `"; "`). |
| `aegis_llm/main.py` | No exception handlers; imports `create_app` only. |

**Gap assessment:** For 04B, there is no “missing handler” for body validation: failures already map to **400** + `invalid_request_error`. If coordinators want **422** for pure validation vs **400** for semantic errors, that would be an intentional policy change, not a fix for absence of handling.

---

## Test / smoke / example payloads — undocumented keys

**Finding:** After ripgrep under `tests/` and `scripts/` for `POST` targets `/v1/chat/completions` and `/v1/embeddings`, **no fixture was found that adds top-level keys outside the current schemas** (e.g. no `tools`, `user`, `seed`, `frequency_penalty`).

Representative payloads are schema-minimal, for example:

| Location | What appears | Relative to “extra keys” |
|----------|----------------|---------------------------|
| `tests/test_chat.py` (e.g. 25–28, 43, 88–99, 125) | `model`, `messages`, optional `stream`; multipart `content` entries with `type`, `text` | Keys on **messages** are only `role` / `content`; `type`/`text` are **inside** `content` list elements (untyped dicts). |
| `tests/test_embeddings.py` (e.g. 26, 54, 100, 114) | `model`, `input`; optional `encoding_format`, `dimensions` | All declared on `EmbeddingsRequest`. `encoding_format: "base64"` is **invalid enum**, not an extra key (`tests/test_embeddings.py:100`). |
| `tests/test_hardening.py:37` | chat + `stream` | Declared. |
| `tests/test_integration_live.py:120–124` | chat + `stream` | Declared. |
| `tests/test_auth.py:50` | embeddings minimal | Declared. |
| `scripts/smoke_compose.sh` (inline Python ~76–81) | chat + `stream` | Declared. |
| `examples/curl_examples.sh:11,16` | chat / embeddings minimal | Declared. |

**Implication:** Turning on `extra="forbid"` for `EmbeddingsRequest` (and likely `ChatCompletionRequest` at top level) should **not** break current repository tests as written; risk moves to **external** OpenAI-shaped clients.

---

## `API_CONTRACT.md` mismatch risk (ignore → forbid)

**Chat (`§ POST /v1/chat/completions`):** States that `ChatCompletionRequest` / `ChatMessage` use `extra="ignore"` and tables label “Any other top-level JSON key” and “Any other key” on messages as **Ignored**. Forbid on either model **contradicts** those rows until 04C updates the contract.

**Embeddings (`§ POST /v1/embeddings`):** Row “Other keys | **Ignored**” — same story: forbid on `EmbeddingsRequest` requires contract text to **Rejected (400)** (or equivalent) for unknown keys.

**Non-stream validation sentence** (chat §): Already claims unknown/bad body → **400** `invalid_request_error`; that remains true; only the **definition** of “bad” expands when unknown keys become validation errors.

---

## Recommendation — first model to tighten

| Choice | Risk | Rationale |
|--------|------|-----------|
| **`EmbeddingsRequest` → `extra="forbid"`** | **Low** (repo); **medium** (wild clients) | Smallest field surface; upstream mapping is a thin pass-through; tests already avoid stray keys. Validates 04B plumbing with limited blast radius. |
| `ChatCompletionRequest` first | **High** | OpenAI SDKs and UIs commonly add `user`, `tools`, penalties, `response_format`, `seed`, etc.; forbid without an allow-list or captured payloads is likely to break integrations. |
| `ChatMessage` first | **High** | Real threads often include `name`, `tool_calls`, `function_call`; today those are silently dropped per contract — forbid would reject those bodies immediately. |

---

## Defer list — keys / clients likely to break if forbid lands early on chat

- **Top-level chat (OpenAI-shaped):** `user`, `seed`, `tools`, `tool_choice`, `functions`, `function_call`, `response_format`, `frequency_penalty`, `presence_penalty`, `logit_bias`, `n`, `logprobs`, `top_logprobs`, `parallel_tool_calls`, `metadata`, `service_tier`, and any future SDK defaults.
- **Per-message:** `name`, `tool_calls`, `function_call`, `audio` / `refusal` / other multimodal metadata (even when ineffective here).
- **Embeddings (if tightening embeddings):** OpenAI optional **`user`**; less common extras (`encoding_format` other than `float` is already rejected by type, not by `extra`).

**Operational note:** Plan §4 and parent brief call for capturing **Open WebUI** / SDK payloads before chat-level forbid; this audit did not substitute for that traffic capture.

---

## Files referenced

- `aegis_llm/schemas.py`
- `aegis_llm/routes/openai.py`
- `aegis_llm/routes/health.py`
- `aegis_llm/app.py`
- `aegis_llm/main.py`
- `docs/API_CONTRACT.md`
- `tests/test_chat.py`, `tests/test_embeddings.py`, `tests/test_hardening.py`, `tests/test_integration_live.py`, `tests/test_auth.py`
- `scripts/smoke_compose.sh`, `examples/curl_examples.sh`

---

## Implementation note (2026-04-13)

`EmbeddingsRequest` in `aegis_llm/schemas.py` now uses `ConfigDict(extra="forbid")` (top-level unknown keys → **400** `invalid_request_error` via existing `RequestValidationError` handling). `ChatCompletionRequest` / `ChatMessage` remain `extra="ignore"` in this pass.
