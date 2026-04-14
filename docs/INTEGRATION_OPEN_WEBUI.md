# Open WebUI + AegisLLM Guard

**Doc role:** real-client connection settings, UI/streaming checklists, and Open WebUI quirks—not the product wedge (see [README.md](../README.md)) or the HTTP contract (see [API_CONTRACT.md](./API_CONTRACT.md)).

Manual checklist for **Open WebUI** (or similar OpenAI-shaped UIs) in front of **Guard** with **Ollama** upstream. Use this after Guard is listening and Ollama is running with at least one chat and (for RAG) one embedding model pulled.

## Prerequisites

- Ollama: `ollama serve` reachable (default `http://127.0.0.1:11434`).
- Guard: e.g. `http://127.0.0.1:8765`.
- Ollama **POST /api/embed** available (current Ollama releases; superseded legacy `/api/embeddings` is not used by Guard).

## Connection settings (Open WebUI)

Open WebUI often points at Guard’s **origin only** (no `/v1` suffix) because the UI may append `/v1` to requests, while the **OpenAI Python SDK** example later in this doc sets `base_url` to `.../v1` explicitly—do not mix the two patterns or you risk double `/v1` or broken paths.

1. **OpenAI API** (or equivalent) base URL: point to Guard’s origin, e.g. `http://127.0.0.1:8765` (not Ollama’s port). Many UIs append `/v1` automatically; if yours asks for the full API root, use the same host and ensure paths resolve to Guard’s `/v1/...`.
2. **API key**: leave empty unless you set `AEGISLLM_API_KEYS` on Guard; if set, use `Authorization: Bearer <key>` (Open WebUI “API key” field).
3. **Model list**: should populate from Guard’s `GET /v1/models` (proxied from Ollama tags). If the list is empty, check Guard `/readyz` and Ollama `GET /api/tags`.

## Functional checklist

| Step | Action | Expect |
|------|--------|--------|
| 1 | Open Guard `/healthz` in browser or curl | `{"status":"ok"}` |
| 2 | Open Guard `/readyz` | `{"status":"ready",...}` |
| 3 | In UI, refresh models | At least one model appears |
| 4 | Chat (non-stream) | Reply completes; no indefinite spinner |
| 5 | Chat (stream) | Tokens stream; stream ends cleanly. For a full Iteration 3 §1 pass, see **Streaming verification (Iteration 3)** below (same doc). |
| 6 | RAG / embeddings (if enabled) | Uses `POST /v1/embeddings` against same base; no hang on dead upstream |

## Streaming verification (Iteration 3)

This section is the **manual** streaming pass for the **§1.2 client cap** (Open WebUI + one official SDK). A client counts as **validated** only after every **§1** row is satisfied with evidence and **§1.1** provenance is filled. **Open WebUI UI + wire:** prefer **Tier C Playwright** (`tests/e2e_open_webui/`, marker `open_webui_e2e`) for repeatable browser and Network-tab–class assertions (e.g. streaming `POST` + `text/event-stream` + `[DONE]`); use this checklist for gaps Playwright does not cover yet (failure toasts, buffering quirks). **SDK:** **scripted** runs against real Guard + Ollama (see **`tests/test_integration_live.py`** with `AEGISLLM_LIVE_OLLAMA=1`) may satisfy **wire-level** §1 rows for the **SDK** (or documented automation) if you record job/env provenance alongside results. **Tier A** `pytest` mocks alone do not count as §1 validation.

**Status (agent / CI environment):** No automated §1 validation runs in CI. **Operator (2026-04-11):** Open WebUI **shell** confirmed running (see **Operator attestation** below). **§1 checkboxes** remain **unchecked** until streaming scenarios are executed and wire/UI evidence is recorded in this doc.

### Operator attestation (environment smoke — not §1 validation)

Recorded for **sub-plan 03A** coordinator sign-off of “stack reachable / UI usable,” **without** claiming the normative §1 streaming pass is complete.

| Field | Record |
|-------|--------|
| **When** | 2026-04-11 (operator session) |
| **URL** | `http://127.0.0.1:3000/` |
| **Observed** | Main chat surface (greeting + **Select a model** + composer + suggested prompts). **Chat Controls** open: **Valves** / **System Prompt** / **Advanced Params**; **Stream Chat Response** present (value **Default**). |
| **Not claimed** | No §1 **Start / Incrementality / Termination / Failure** wire or UI evidence recorded here yet; no filled **§1.1** version digest. |
| **Version hygiene** | UI may advertise a newer release in-app (e.g. update banner) while Compose pins a specific image — before ticking §1, set **§1.1 — Version** to the **running container** tag or `repo@sha256:…`, not the banner alone. |

### Normative criteria (§1) — checklist header

The §1 criteria in the table below are normative for this checklist. If server-side streaming semantics change, align this table with **`docs/API_CONTRACT.md`** (streaming / SSE) and the implementation in **`aegis_llm/`**.

A pass is **validated** for that client only if **all** rows were observed and recorded (checkboxes OK):

| Criterion | Meaning |
|-----------|---------|
| **Start** | `200`, `text/event-stream`, first `data:` as expected |
| **Incrementality** | ≥ two content-bearing chunks (or equivalent visible token steps) |
| **Termination** | Clean end; normal path includes **`[DONE]`** on wire or SDK completion without hang |
| **Failure** | At least one failure path where feasible; **UI vs wire** summarized |

### Provenance template (§1.1)

For each client subsection, record:

| Field | Your value |
|-------|------------|
| **Client name** | _e.g. Open WebUI / OpenAI Python SDK_ |
| **Rough version** | _Open WebUI: image tag or app version; SDK: `pip show openai`_ |
| **Date** (or Guard / release id) | _e.g. 2026-04-11 + commit or image digest_ |

---

### Open WebUI — minimum scenarios (parent plan §4.1)

Run against a running Guard + Ollama with the same **Connection settings** as above.

1. **Stream on / stream off** — Toggle streaming in the UI if available. **Stream on:** tokens should arrive incrementally; spinner clears; final text not obviously truncated. **Stream off:** single completion; no indefinite spinner.
2. **Failure during stream** — Provoke upstream failure or stop Ollama mid-reply where safe (e.g. stop `ollama serve` or use a model/load scenario that errors). Record **what the UI showed** vs **what appeared on the wire** (browser devtools → Network → the chat completion request: `text/event-stream` lines, error `data:` payloads, trailing `[DONE]` per `sse_error_termination` where applicable).
3. **Quirks** — Note Open WebUI–specific issues: base URL with or without `/v1`, model list refresh, timeouts, any UI that buffers the entire stream until the end (affects **Incrementality** observation).

Record wire notes and quirks in the **Wire notes** and **Quirks observed** paste blocks below (operator or automation).

#### Wire notes — stream on / stream off (subagent / operator paste)

_Role **03A-O1**. Redact secrets; truncate very long `data:` lines._

```text
### Supplemental: direct Guard SSE (curl, not Open WebUI UI)

**healthz** (`curl -sS --max-time 5 http://127.0.0.1:8765/healthz`): `{"status":"ok"}`

**readyz** (`curl -sS --max-time 8 http://127.0.0.1:8765/readyz`): `{"status":"ready","backend":"ollama"}`

**models** (`GET /v1/models`): valid JSON `{"object":"list","data":[]}` — no model `id` in list; streaming POST skipped (need at least one Ollama tag / model for Guard to expose).

Open WebUI normative §1 rows still require browser Network evidence; this block is backend correlation only.
```

#### Wire notes — failure during stream (subagent / operator paste)

_Role **03A-O2**._

```text
Blocked in automated wave (2026-04-13): failure scenario requires operator-controlled Open WebUI + Network capture while upstream stops mid-stream. No §1 Failure tick.
```

#### Quirks observed (subagent / operator paste)

_Use for bullets not captured above (role **03A-O1** may fold short quirks into stream notes instead)._

```text

```

**§1 checklist — Open WebUI** (map each row to the table above):

- [ ] **Start** — _Pending operator execution (2026-04-11)_
- [ ] **Incrementality** — _Pending operator execution (2026-04-11)_
- [ ] **Termination** — _Pending operator execution (2026-04-11)_
- [ ] **Failure** — _Pending operator execution (2026-04-11)_

**§1.1 provenance — Open WebUI** (fill when the pass is run):

| Field | Value |
|-------|-------|
| Client name | Open WebUI |
| Version | `ghcr.io/open-webui/open-webui:v0.5.7@sha256:c5337440053c18df15488ec6877d8d87db37ea21bb976a5c2526a1b6a20f0ecd` (running container `aegis_llm-open-webui-1`; `docker inspect` `.Image`; no `.RepoDigests` on this image) |
| Date / Guard context | 2026-04-13 UTC; repo git `a79ad99a5f6a0bc3ed0d6850ce7ae416128ea62d` |

---

### Second client — OpenAI Python SDK (`stream=True`)

### Explicit deferral — OpenAI Python SDK (Iteration 3)

The hands-on OpenAI Python SDK `stream=True` §1 execution in this section is **deferred** so operator time can prioritize Open WebUI browser wire evidence and UI-visible streaming behavior under Iteration 3’s capped-client scope. Per **§1.2** of the parent plan, that choice is acceptable when the reason and unblock path are explicit rather than omitted. **Unblocking** the SDK leg means running the `pip install` and Python example below once Guard and Ollama are in a stable configuration, observing Start through Failure against the §1 table, then recording results in the SDK §1 checkboxes and **§1.1** using `pip show openai`, the active Python version, and date or Guard context. For complementary **wire-level** automation (httpx consumer, not the official SDK), you may use `tests/test_integration_live.py::test_live_guard_chat_completion_stream` with `AEGISLLM_LIVE_OLLAMA=1` and the env vars documented in that test’s docstring; that test does not by itself satisfy SDK-specific checklist rows unless you also capture SDK-side observations. The Open WebUI §1 block earlier in this document can be completed **independently** of the SDK pass. Until the deferred run happens, the SDK rows below stay open and this doc does **not** claim §1 validation for the Python client.

Minimal pattern: point the official client at Guard’s OpenAI-compatible root and align the API key with `AEGISLLM_API_KEYS` (use a placeholder or empty string when Guard has no keys).

```bash
pip install "openai>=1.0"
```

```python
import os
from openai import OpenAI

# Guard origin: host + port only here — do NOT include `/v1` in AEGISLLM_GUARD_BASE_URL (this snippet appends `/v1` once).
base = os.environ.get("AEGISLLM_GUARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
base_url = f"{base}/v1"

client = OpenAI(
    base_url=base_url,
    # Must match Guard: omit or "" when no keys; otherwise same token as AEGISLLM_API_KEYS
    api_key=os.environ.get("OPENAI_API_KEY", ""),
)

stream = client.chat.completions.create(
    model="<model-from-GET-/v1/models>",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    stream=True,
)
for event in stream:
    # Inspect event.choices[0].delta for incremental content.
    print(event)
# Iterator exhaustion = SDK-side completion; cross-check raw wire with curl if you need [DONE] visibility.
```

**§1 checklist — OpenAI Python SDK:**

- [ ] **Start** — _Pending operator execution (2026-04-11)_
- [ ] **Incrementality** — _Pending operator execution (2026-04-11)_
- [ ] **Termination** — _Pending operator execution (2026-04-11)_
- [ ] **Failure** — _Pending operator execution (2026-04-11)_ (e.g. stop upstream mid-stream; compare exception / final chunks vs Network trace or `httpx` logging)

**§1.1 provenance — OpenAI Python SDK** (fill when the pass is run):

| Field | Value |
|-------|-------|
| Client name | OpenAI Python SDK |
| Version | Python 3.14.2 (`.venv/bin/python -V`); `openai` not installed in `.venv` (`pip show openai` empty) |
| Date / Guard context | 2026-04-13 UTC; repo git `a79ad99a5f6a0bc3ed0d6850ce7ae416128ea62d` |

---

**Future work (one line):** Additional UIs or SDKs are out of scope for Iteration 3; if another client becomes important, repeat this §1 + §1.1 block in a linked doc and cap clients per release planning.

## If something fails

- **Hang on model list**: UI may be waiting on OpenAI-shaped `GET /v1/models`; confirm Guard returns JSON within connect/read timeouts (see `AEGISLLM_CONNECT_TIMEOUT` / `AEGISLLM_READ_TIMEOUT`).
- **401/403**: Guard auth is enabled; set the same key in the UI or clear `AEGISLLM_API_KEYS`.
- **502/504 on chat or embeddings**: Ollama down or slow; check Ollama logs and Guard stderr diagnostics line printed at startup.

## Compatibility note

Guard implements a **subset** of the OpenAI API (chat completions, models, embeddings). It does **not** implement every OpenAI feature (tools, audio, Responses API, etc.). Position the stack honestly: **reliability gateway for Ollama**, not a full OpenAI mirror.
