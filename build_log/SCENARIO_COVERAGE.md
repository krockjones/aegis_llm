# Scenario coverage — AegisLLM Guard

Maps **why the service exists** (product / wedge scenarios) to **automated tests** and **optional live checks**. **Streaming:** Tier B **real-resource** E2E (Guard + Ollama, SSE) is encouraged where bounded—see [TESTING_NOTES.md](./TESTING_NOTES.md) *Streaming — real-resource E2E*. Use this when adding features so tests stay tied to operator-visible outcomes, not only line coverage.

**First run / adoption:** operator step-by-step is [../docs/GETTING_STARTED.md](../docs/GETTING_STARTED.md).

For layer definitions (unit vs ASGI vs live), see [TESTING_NOTES.md](./TESTING_NOTES.md).

## Scenarios → tests

| Scenario (operator / integrator view) | Primary tests (mocked Ollama unless noted) | Opt-in live |
|---------------------------------------|--------------------------------------------|-------------|
| **OpenAI-shaped `/v1/models`** for UIs and SDKs | `test_openai_contract.py::test_v1_models_openai_client_shape` (`scenario: openai-models-shape`); `test_models.py::test_v1_models` | Compose + curl `GET /v1/models` |
| **Chat completions** (JSON + errors) | `test_chat.py::test_chat_completions_non_stream`, `test_chat_completions_*` (validation, upstream error, content-list) | Same + Open WebUI against Guard |
| **SSE / NDJSON streaming** to clients | `test_chat.py::test_chat_completions_stream` (`scenario: chat-stream-sse`); `test_hardening.py::test_chat_stream_upstream_http_error` (`scenario: chat-stream-sse-error`) | Real model: `test_integration_live.py::test_live_guard_chat_completion_stream` with `AEGISLLM_LIVE_OLLAMA=1`; **`scripts/smoke_compose.sh`** streaming step after models; stream in UI or `curl -N`. **Iteration 3 manual checklist** (operator opt-in): [../docs/INTEGRATION_OPEN_WEBUI.md](../docs/INTEGRATION_OPEN_WEBUI.md) (“Streaming verification”). |
| **Embeddings** (single, batch, dimensions, errors; **unknown top-level JSON keys → 400** `invalid_request_error`) | `test_embeddings.py::*` (`scenario: embeddings-single` on first test); `test_embeddings_rejects_unknown_top_level_key` — `EmbeddingsRequest` is `extra="forbid"` ([`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md) `POST /v1/embeddings`) | `docker-compose` embeddings example in README |
| **Bearer API keys** on sensitive routes | `test_auth.py::*`; `test_hardening.py::test_auth_*` | Set keys in env; `curl` with/without `Authorization` |
| **Public liveness** (`/healthz`) vs **upstream readiness** (`/readyz`) | `test_health.py::*`; `test_hardening.py::test_readyz_*` | Hit both endpoints against running stack |
| **Timeouts / connect / 502 mapping** | `test_hardening.py::test_v1_models_upstream_*`, `test_readyz_upstream_timeout`, `test_v1_models_invalid_json_body_returns_502`, embeddings timeout tests | Stress or block upstream in compose |
| **Config guardrails** (bad upstream URL scheme) | `test_hardening.py::test_load_settings_rejects_bad_upstream_scheme` | Misconfigure `.yaml` / env in staging |
| **Request ID** propagation | `test_hardening.py::test_x_request_id_roundtrip` | Inspect response headers from curl |
| **Deployment posture** (non-loopback + no keys → WARNING logs; CORS; log level) | `test_security_posture_warnings.py::*`; `test_main.py::test_main_emits_deployment_warning_wide_bind_no_keys` | Run `aegis-llm` with `0.0.0.0` and empty keys; subprocess cases in `test_security_posture_warnings.py` |
| **CLI / process entry** (invalid port, uvicorn wiring) | `test_main.py::test_main_exits_2_on_invalid_listen_port`, `test_main_success_ordering_and_uvicorn_call` | Manual smoke |
| **Real Ollama reachability** (not mocked) | — | `test_integration_live.py::test_live_ollama_tags_reachable` with `AEGISLLM_LIVE_OLLAMA=1` |
| **Running Guard + Ollama** (headers on real HTTP) | — | `test_integration_live.py::test_live_guard_readyz_and_v1_models_headers` with `AEGISLLM_LIVE_OLLAMA=1` and Guard up; or **`scripts/smoke_compose.sh`** / **`.github/workflows/aegis-llm.yml`** compose job |
| **Open WebUI UI shell (Tier C)** | `tests/e2e_open_webui/test_open_webui_reachable.py` (`scenario: open-webui-reachable`; `open_webui_e2e`) | `docker compose --profile tier-c up`; `AEGISLLM_OPEN_WEBUI_E2E=1`; `pip install -e ".[e2e]"`; `python -m playwright install`; see [../tests/e2e_open_webui/README.md](../tests/e2e_open_webui/README.md) |
| **Guard /healthz in browser (Tier C)** | `tests/e2e_open_webui/test_guard_health_browser.py` (`scenario: guard-health-browser`; `open_webui_e2e`) | Same as Tier C; Guard must be reachable at `AEGISLLM_GUARD_BASE_URL` (default `http://127.0.0.1:8765`) |
| **Guard /readyz in browser (Tier C)** | `tests/e2e_open_webui/test_guard_readyz_browser.py` (`scenario: guard-readyz-browser`; `open_webui_e2e`) | Accepts `200` or `503`; JSON `status` `ready` / `not_ready` |
| **Guard /v1/models in browser (Tier C)** | `tests/e2e_open_webui/test_guard_v1_models_browser.py` (`scenario: guard-v1-models-browser`; `open_webui_e2e`) | JSON list shape; optional `AEGISLLM_E2E_BEARER` when Guard auth is on |
| **Open WebUI streaming POST (Tier C)** | `tests/e2e_open_webui/test_open_webui_stream_network.py` (`scenario: open-webui-stream-network`; `open_webui_e2e`) | Requires at least one model from Guard `/v1/models` (pull in Ollama); skips on auth gate; asserts `text/event-stream`, multiple `data:` frames, `[DONE]` |
| **Contract streaming doc sentinel** | `tests/test_contract_streaming_sentinel.py` (`scenario: contract-streaming-sentinel`) | Default `pytest`; guards `API_CONTRACT.md` streaming section against forbidden universal-client wording |

## Optional `@pytest.mark.scenario`

A small number of tests carry **`@pytest.mark.scenario("<id>")`** so you can grep or filter by product thread:

```bash
uv run pytest tests/ -m scenario -q
```

Registered in `pyproject.toml` as `scenario`. **Not every test needs a scenario mark** — extend incrementally when a test clearly anchors a user-visible story (add the same `id` here in the table above).

## Gaps (by design or backlog)

| Area | Today | Stretch |
|------|--------|---------|
| Real NDJSON chunk boundaries vs respx | Mocked streams only | Live stream test against Ollama |
| Docker DNS / TLS | Compose smoke hits Guard→`ollama` on the compose network | Staging TLS |
| CORS `OPTIONS` | Not asserted | Add if browser clients require it |
| Full `uvicorn` signal handling | Mocked `uvicorn.run` | Manual or separate process test |
| SSE / stream beyond respx | Mocked NDJSON upstream in pytest; manual Iteration 3 checklist for real UIs | ASGI-level stream consumer test; Bearer + streaming; mid-stream client disconnect — parent PLAN §4.4 backlog unless incident-driven |

Treat this file as **living**: when you add a user-facing route or behavior, add a row (or extend an existing scenario) and at least one automated test before merging.
