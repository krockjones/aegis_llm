# E2E / integration coverage assessment — AegisLLM Guard

**Scope:** Streaming-focused end-to-end and integration signals, with non-streaming called out where the repo differs. **Sources:** `tests/test_integration_live.py`, `scripts/smoke_compose.sh`, `build_log/SCENARIO_COVERAGE.md`, `build_log/TESTING_NOTES.md`, `build_log/testing_tiers/HUB.md`, `tests/e2e_open_webui/README.md`, `.github/workflows/aegis-llm.yml`, `pyproject.toml` pytest markers.

---

## 1. Executive summary

Default automation is **Tier A–style**: in-process ASGI tests with **mocked Ollama** (`respx`), excluding anything marked `integration` (`pytest tests/ -q -m "not integration"` in `.github/workflows/aegis-llm.yml`). **Tier B** is represented by **`scripts/smoke_compose.sh`** in CI (after pytest) and by **opt-in** `tests/test_integration_live.py` when `AEGISLLM_LIVE_OLLAMA=1` with a reachable Guard and upstream. **Streaming** against a real stack is covered by compose smoke (full-body read) and `test_live_guard_chat_completion_stream`; **non-streaming** chat is **not** exercised in live integration tests—only via mocked routes (e.g. `tests/test_chat.py::test_chat_completions_non_stream`). **Tier C** adds Playwright checks (`tests/e2e_open_webui/`, marker `open_webui_e2e`): shell load, Guard `/healthz`, and **streaming chat** (`test_open_webui_stream_network` asserts SSE via the browser’s completion request). Default CI **deselects** `open_webui_e2e`. **Default CI** also runs **`tests/test_contract_streaming_sentinel.py`** on `API_CONTRACT.md` streaming wording. **RAG** and rich failure UX in Open WebUI remain manual or future tests.

---

## 2. Coverage surface table

| Surface | Automated? | Opt-in? | Gaps |
|---------|------------|---------|------|
| **ASGI + mocked Ollama — chat non-stream** | Yes (`tests/test_chat.py::test_chat_completions_non_stream`, `test_chat_completions_upstream_error`, validation tests) | No (default CI) | Not real NDJSON/chunk boundaries vs production Ollama |
| **ASGI + mocked Ollama — chat SSE stream** | Yes (`tests/test_chat.py::test_chat_completions_stream`; `tests/test_hardening.py::test_chat_stream_upstream_http_error`) | No | Mocked upstream only; no incremental client consumption assertions vs wire |
| **ASGI — `/v1/models`, health, embeddings, auth** | Yes (`tests/test_models.py`, `tests/test_health.py`, `tests/test_embeddings.py`, `tests/test_auth.py`, `test_openai_contract.py`, etc.) | No | Same: no real Docker DNS/TLS |
| **Live Ollama `GET /api/tags`** | Yes | **Yes** — `AEGISLLM_LIVE_OLLAMA=1`; `tests/test_integration_live.py::test_live_ollama_tags_reachable` | Not run in default CI; optional `AEGISLLM_UPSTREAM_BASE_URL` |
| **Live Guard — `/healthz`, `/readyz`, `GET /v1/models` + disclosure headers** | Yes | **Yes** — same env; `test_live_guard_readyz_and_v1_models_headers` | Skips on connect failure or `/readyz` 503; no Bearer path in this test (401/403 not the focus here) |
| **Live Guard — `POST /v1/chat/completions` `stream: true` (full body)** | Yes | **Yes** — `test_live_guard_chat_completion_stream` | Skips if Guard down, `readyz` 503, empty models, or `GET /v1/models` 401/403 without token; **no** live **non-stream** chat test |
| **Docker Compose E2E (Ollama + Guard)** | Yes (`compose-smoke` in `.github/workflows/aegis-llm.yml` → `scripts/smoke_compose.sh`) | No (runs on PR when paths match workflow rules) | Waits for `/readyz` 200; `GET /v1/models` + headers; stream step **skipped** if `data[]` empty (exit 0); no Guard-auth scenario; no embeddings in script |
| **Open WebUI / browser** | Yes | **Yes** — `AEGISLLM_OPEN_WEBUI_E2E=1`, `.[e2e]`, `python -m playwright install`; compose `--profile tier-c` | Shell + Guard `/healthz` + **streaming POST** (`test_open_webui_stream_network`); skips if no models or auth gate; RAG / failure UX not automated |

---

## 3. Tier A vs B vs C — alignment with repo reality

| Tier | Policy / intent (`build_log/TESTING_NOTES.md`, `build_log/testing_tiers/HUB.md`) | What exists in-repo |
|------|----------------------------------------------------------------------------------|---------------------|
| **A** | Fast ASGI tests with mocked Ollama (`respx`); default PR CI | **Implemented:** broad `tests/*.py` suite run with `-m "not integration"` in `.github/workflows/aegis-llm.yml`. Streaming: `test_chat_completions_stream`, `test_chat_stream_upstream_http_error`. Non-stream: `test_chat_completions_non_stream` and related. Orchestration docs: `build_log/testing_tiers/LEAD_TIER_A.md`, `WORKER_A1.md`–`A3.md`. |
| **B** | Real Guard + real Ollama; streaming E2E encouraged; must skip cleanly | **Implemented:** `tests/test_integration_live.py` (module `pytestmark = pytest.mark.integration`) — `test_live_ollama_tags_reachable`, `test_live_guard_readyz_and_v1_models_headers`, `test_live_guard_chat_completion_stream`. **CI:** `scripts/smoke_compose.sh` in `compose-smoke` job. **Not in default pytest CI:** live module excluded by `-m "not integration"`. Docs: `LEAD_TIER_B.md`, `WORKER_B1.md`–`B3.md`. |
| **C** | Browser / Open WebUI automation; optional; pinned images | **`tests/e2e_open_webui/`** — reachability, Guard health, **streaming chat network** (`test_open_webui_stream_network`); `docker-compose.yml` profile `tier-c`; `pyproject` extra `e2e`. **Not** default CI for Tier C. RAG / failure UX still manual or future workers. |

---

## 4. Top five prioritized recommendations

1. **Must — Keep `integration` marker and CI filter aligned**  
   Any new live or external-service test should stay behind `pytest.mark.integration` (or equivalent) so `pytest tests/ -q -m "not integration"` in `.github/workflows/aegis-llm.yml` remains a reliable fast gate, matching `pyproject.toml` marker documentation.

2. **Must — Treat compose stream step as “best effort” when models are empty**  
   `scripts/smoke_compose.sh` exits successfully when `data[]` is empty (stream smoke skipped). Operators relying on stream proof in CI should ensure the Ollama image/step pulls a model or accept that the stream assertion may not run.

3. **Should — Add an opt-in live non-stream chat completion test (if product-critical)**  
   Today, real-stack chat is **streaming-only** in `test_integration_live.py`. If integrators care about `stream: false` against Ollama through Guard, add a sibling test with the same skip semantics and document env vars in `build_log/TESTING_NOTES.md`.

4. **Should — Exercise Bearer + live `GET /v1/models` + stream in one documented command**  
   `test_live_guard_chat_completion_stream` documents skipping on 401/403 for models without a Bearer token; a small doc or example env block (README or `TESTING_NOTES.md`) showing `httpx`/`curl` with `Authorization` would close the “keys enabled” path without forcing it in CI.

5. **Nice — Tier C nightly when funded**  
   `tests/e2e_open_webui/README.md` outlines a scheduled job; stream smoke exists—extend with RAG, auth flows, and failure UX when stable selectors exist.

---

## 5. Explicit “not covered” (honest)

- **Live / compose automated `POST /v1/chat/completions` with `stream: false`** — not in `tests/test_integration_live.py` or `scripts/smoke_compose.sh`.
- **Automated Open WebUI RAG** — not implemented. **Streaming chat** — partial (`test_open_webui_stream_network`); failure UX and incrementality in DOM not asserted.
- **`test_integration_live.py` in default GitHub Actions pytest job** — workflow uses `-m "not integration"`; live tests are not executed in CI unless separately invoked with env + services.
- **TLS termination, real certificates, and production-style hostnames** — called out as gaps in `build_log/SCENARIO_COVERAGE.md` / `build_log/TESTING_NOTES.md`; not asserted here.
- **CORS `OPTIONS`** — `build_log/SCENARIO_COVERAGE.md` lists as not asserted.
- **Incremental SSE consumption** (line-by-line while upstream generates) — compose script and `test_live_guard_chat_completion_stream` read the **full** response body before assertions.
- **Mid-stream client disconnect, backpressure, multi-turn UI flows** — backlog / manual territory per `build_log/SCENARIO_COVERAGE.md` gaps table, not automated in cited files.
- **`uvicorn` signal handling / full process lifecycle** — noted as mocked or manual in `build_log/TESTING_NOTES.md`.
- **Dedicated workflow file under `zed_toolkit/services/aegis_llm/.github/`** — CI lives at repo root `.github/workflows/aegis-llm.yml` only (no additional `*aegis*` workflows found under the service directory in the search performed).

---

**Written path:** `zed_toolkit/services/aegis_llm/build_log/ASSESSMENT_E2E_INTEGRATION_COVERAGE.md`
