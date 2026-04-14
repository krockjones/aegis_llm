# Tier C — Open WebUI browser E2E (Playwright)

## Purpose

**Browser-driven** checks against **Open WebUI** in front of **AegisLLM Guard** with **Ollama** upstream. Tier C validates UI-level behavior that Tier A mocks and Tier B HTTP checks do not cover alone.

See the repository [README.md](../../README.md) **Tests** section for how Tier C fits into the default CI filter and optional Playwright runs.

## What is implemented today

| Piece | Location |
|-------|----------|
| **Compose (Open WebUI + existing stack)** | [`docker-compose.yml`](../../docker-compose.yml) — service `open-webui` with profile **`tier-c`** (pinned image `ghcr.io/open-webui/open-webui:v0.5.7`, `OPENAI_API_BASE_URL` → Guard `/v1`). |
| **Smoke tests** | [`test_open_webui_reachable.py`](./test_open_webui_reachable.py) — Open WebUI shell. [`test_guard_health_browser.py`](./test_guard_health_browser.py) — `GET /healthz`. [`test_guard_readyz_browser.py`](./test_guard_readyz_browser.py) — `GET /readyz` (`200`/`503`). [`test_guard_v1_models_browser.py`](./test_guard_v1_models_browser.py) — `GET /v1/models` JSON list (`AEGISLLM_E2E_BEARER` if Guard uses `AEGISLLM_API_KEYS`). [`test_open_webui_stream_network.py`](./test_open_webui_stream_network.py) — model picker if needed, composer ``#chat-input`` (TipTap on v0.5.7), ``#send-message-button`` or Enter, then streaming `POST` (SSE + `[DONE]`); skips if no models or auth gate. |
| **Marker** | `open_webui_e2e` — excluded in CI via `-m "not open_webui_e2e"` (see repo `.github/workflows/aegis-llm.yml`). |

## Not in default CI

These tests are **opt-in**. They are **not** part of the default `pytest` / PR matrix: install **`.[e2e]`**, Playwright browsers, set **`AEGISLLM_OPEN_WEBUI_E2E=1`**, and bring up Open WebUI (e.g. `docker compose --profile tier-c up -d`).

## Run locally (minimal)

From the repository root (directory containing `docker-compose.yml`):

```bash
docker compose --profile tier-c up -d --build
# Wait until Open WebUI responds on http://127.0.0.1:3000 (first boot can take a minute).

pip install -e ".[e2e]"
python -m playwright install

export AEGISLLM_OPEN_WEBUI_E2E=1
export OPEN_WEBUI_BASE_URL=http://127.0.0.1:3000   # optional; this is the default
export AEGISLLM_GUARD_BASE_URL=http://127.0.0.1:8765   # optional; Guard origin for /healthz test
# export AEGISLLM_E2E_BEARER=<same as AEGISLLM_API_KEYS token>  # when Guard auth is enabled

pytest tests/e2e_open_webui/ -q -m open_webui_e2e
```

Use `docker compose --profile tier-c down` (or `down -v` if you want a clean Open WebUI volume) when finished.

## Integration manual

Operator checklist, connection settings, and streaming §1 criteria:

[**`docs/INTEGRATION_OPEN_WEBUI.md`**](../../docs/INTEGRATION_OPEN_WEBUI.md)

## Pinning policy (CI and reproducible runs)

Do **not** rely on unpinned `:latest` (or equivalent floating tags) for **any** component when Tier C runs in **CI** or when results must be comparable across runs.

| Component | Pinning expectation |
|-----------|---------------------|
| **Open Web UI** | Image **digest** (not only a mutable tag). Record `repo@sha256:…` in job env or compose file used by the pipeline. |
| **Browser / automation** | Pin **browser channel** and driver/runtime versions (e.g. Playwright version + pinned browser build) in lockstep with the test harness. |
| **Guard (aegis_llm)** | Pin **image digest** or **git SHA** + container tag used in the job. |
| **Ollama** | Pin **server image digest** (or exact release) and **model tags** pulled for the run (no implicit “pull latest” in CI without a recorded digest). |

Local quick iteration may use moving tags; **CI and nightly evidence must cite digests or exact versions** in provenance (see §1.1 in the integration doc).

## Optional nightly job (outline)

When implemented, coordinators can add a **scheduled workflow** (e.g. nightly) that:

1. Spins up **pinned** Ollama + Guard + Open Web UI (compose or CI services) using digests/tags from this README or a checked-in `compose.tier-c.yaml`.
2. Installs **pinned** Playwright (or chosen runner) and runs `tests/e2e_open_webui/` only in that job (not on every PR).
3. Uploads traces/screenshots/logs and fills **provenance** (Open Web UI version, digests, Guard commit) per [`INTEGRATION_OPEN_WEBUI.md`](../../docs/INTEGRATION_OPEN_WEBUI.md).

The default **aegis-llm** GitHub workflow still **does not** run Tier C; add a **scheduled** job that installs `.[e2e]`, runs `python -m playwright install --with-deps` (Linux) so **Chrome Headless Shell** matches the driver, brings up compose with `--profile tier-c`, and runs `pytest tests/e2e_open_webui/ -m open_webui_e2e` when you want nightly evidence.
