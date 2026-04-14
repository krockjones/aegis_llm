# Testing notes — AegisLLM Guard

## Pyramid (short)

| Layer | What runs | Typical files |
|-------|-----------|---------------|
| **Unit** | Predicates, config, stderr helpers | `test_security_posture_warnings.py`, parts of `test_hardening.py` |
| **ASGI + respx** | Full `create_app`, lifespan, middleware; Ollama **mocked** | `test_chat.py`, `test_models.py`, `test_embeddings.py`, `test_auth.py`, `test_health.py`, most of `test_hardening.py` |
| **Process / live (opt-in)** | `main()` subprocess, real Ollama | `test_main.py`, `test_integration_live.py` |

## Integration value

**In-process ASGI tests** give the best ROI for routing, middleware order, lifespan `httpx` client, and error mapping without pulling models.

**Gaps they intentionally do not cover:** real NDJSON chunk boundaries, Docker DNS, TLS, `uvicorn` signal handling — use opt-in tests below.

## Opt-in live checks

| Env | Behavior |
|-----|----------|
| `AEGISLLM_LIVE_OLLAMA=1` | Runs `test_integration_live.py`: raw Ollama `GET /api/tags` at `AEGISLLM_UPSTREAM_BASE_URL` (default `http://127.0.0.1:11434`), and **Guard** `GET /healthz`, `GET /readyz`, `GET /v1/models` (expects `X-AegisLLM-*` headers) at `AEGISLLM_GUARD_BASE_URL` (default `http://127.0.0.1:8765`). Also **Tier B** `POST /v1/chat/completions` with `stream: true` (`test_live_guard_chat_completion_stream`): discovers a model id from `/v1/models`, reads the full SSE body via **httpx**, asserts `chat.completion.chunk` and `[DONE]` (and `text/event-stream` when `Content-Type` is present). Guard must be running separately; tests **skip** if Guard is unreachable, `/readyz` is 503, models list is empty, or `/v1/models` is 401/403 without a Bearer token. |

**CI:** `pytest -m "not integration and not open_webui_e2e"` for fast jobs (see `.github/workflows/aegis-llm.yml`). Repo workflow also runs `scripts/smoke_compose.sh` (Docker Compose E2E). Manual live: `AEGISLLM_LIVE_OLLAMA=1 uv run pytest tests/ -q`. Tier C: see [tests/e2e_open_webui/README.md](../tests/e2e_open_webui/README.md).

## Streaming — real-resource E2E / integration (policy)

**Inflection:** Iteration 3 **explicitly allows** automated tests that exercise **real** Guard→Ollama **SSE** streaming (not only `respx` mocks), alongside manual Open WebUI / SDK checklists.

| Tier | What | When |
|------|------|------|
| **A** | ASGI + mocked Ollama (`respx` NDJSON) | Every PR; fast. |
| **B** | Real Ollama + real Guard: `POST /v1/chat/completions` with `stream: true`; assert incremental `data:` lines + `[DONE]` (and error SSE where feasible). Use **httpx** stream, **curl -N**, or compose smoke. | Same opt-in flags as other live checks: `AEGISLLM_LIVE_OLLAMA=1` and `AEGISLLM_GUARD_BASE_URL` (see `test_live_guard_chat_completion_stream`); compose workflow or nightly—**must skip** if endpoints unreachable. |
| **C** | Browser / Open WebUI (`tests/e2e_open_webui/`): Playwright vs `OPEN_WEBUI_BASE_URL` (default `http://127.0.0.1:3000`), Guard `/healthz`, and **streaming chat** (`test_open_webui_stream_network`: asserts SSE shape via browser-emitted completion request); compose **`--profile tier-c`** adds `open-webui`. Default CI also runs **`tests/test_contract_streaming_sentinel.py`** on `docs/API_CONTRACT.md` streaming section. | **`AEGISLLM_OPEN_WEBUI_E2E=1`**, `pip install -e ".[e2e]"`, `python -m playwright install`; excluded from PR CI via `-m "not open_webui_e2e"`. |

**Contract / docs:** Tier B runs can be cited in `docs/API_CONTRACT.md` **Operational verification** with **provenance** (job name, Ollama/Guard image digests or versions, date)—same honesty bar as manual §1.1. They **do not** replace Open WebUI **UI** checklist rows unless you add Tier C.

**Guards:** pin Ollama (and Guard) images in compose docs; no Tier B on default PR job unless skips are reliable; prefer `pytest.mark.integration` (or existing convention) so `pytest -m "not integration and not open_webui_e2e"` stays fast.

**Multi-agent layout:** Tier A/B/C **leads + N workers** — see [testing_tiers/HUB.md](./testing_tiers/HUB.md).

## Anti-patterns

- Do not run live tests on every PR without skips and **pinned** Ollama images in compose docs.
- Avoid mocking `create_app` when testing middleware ordering — use the real app fixture in `conftest.py`.

## Scenario traceability

Operator-visible “why we built it” threads (models, chat, embeddings, auth, deployment warnings, live Ollama) are mapped to tests in [SCENARIO_COVERAGE.md](./SCENARIO_COVERAGE.md). Optional `@pytest.mark.scenario("…")` on selected tests is documented there.
