# AegisLLM Guard

**Release status:** Public **alpha** (package v0.2). The HTTP surface and defaults may evolve between releases; treat **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)** and **`tests/`** as the integration source of truth—not every OpenAI client feature is supported or guaranteed.

> **One-liner:** AegisLLM Guard is a **narrow public alpha**: an OpenAI-**shaped** HTTP edge in front of **Ollama** with an **explicitly bounded** API, clearer errors, and operator-focused posture—not a full OpenAI mirror, not a multi-backend platform.

## What this is

A thin **OpenAI-compatible reliability gateway**: HTTP clients speak a familiar **`/v1/...`** surface while **Ollama stays the engine** you already run. **Only Ollama is implemented and supported as an upstream today.** An internal `Backend` protocol exists for structure and tests, not for “pick another vendor” in this release line.

## Where it sits

In front of **one** Ollama HTTP API at **`AEGISLLM_UPSTREAM_BASE_URL`**. Guard does not pull or host models by itself.

## What problem it solves

- **Hung or vague failures** when Open WebUI, SDKs, or agents call Ollama over raw HTTP and the upstream misbehaves or disappears mid-request.
- **“OpenAI-compatible” confusion** where clients assume fields or semantics you do not actually support—Guard documents a **bounded** subset in the contract and validates requests accordingly.
- **Operator blind spots:** readiness vs liveness split, startup signals for risky bind/auth combinations, and logs you can grep without spelunking Ollama internals.

## What it is not

- **Not** a universal local-LLM **platform** or “any backend” gateway.
- **Not** a full OpenAI API mirror or drop-in parity with every SDK feature.
- **Not yet:** multi-backend routing, quotas, tool calling, `encoding_format: base64` for embeddings, or broad compatibility with every OpenAI client feature—see **What it is not yet** under [Alpha release scope](#alpha-release-scope).

**Canonical API boundaries** (supported subset, rejected vs ignored fields, errors): [docs/API_CONTRACT.md](docs/API_CONTRACT.md). OpenAPI at **`/docs`** is descriptive; the contract doc is what integrators should rely on.

---

## Canonical quickstart (recommended)

**Fastest path for a stranger:** Docker Compose (Ollama + Guard on one network). Full step-by-step (start stack, pull a model, `curl` health / readyz / models / first chat, optional stream) lives in **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** under **Path A — Docker Compose (recommended first run)**.

Minimal recap from the **repository root** (where `docker-compose.yml` lives):

1. `docker compose up --build` (add `-d` for detached).
2. In another terminal: `docker compose exec ollama ollama pull llama3.2` (or another tag; use the same name in chat JSON).
3. `curl -sS http://127.0.0.1:8765/healthz` and `http://127.0.0.1:8765/readyz`.
4. First non-stream chat: copy the `curl` from Path A **step 4** in GETTING_STARTED.

Then: optional stream (Path A step 5), **[examples/curl_examples.sh](examples/curl_examples.sh)**, and **[docs/INTEGRATION_OPEN_WEBUI.md](docs/INTEGRATION_OPEN_WEBUI.md)** if you use Open WebUI.

---

## Alpha release scope

Use this section to set expectations—**trust-preserving**, not defensive.

| Topic | Reality in this alpha |
|--------|------------------------|
| **Upstream** | **Ollama-only** at a single configured base URL. No multi-vendor routing. |
| **API** | **Bounded** OpenAI-**shaped** subset—see [docs/API_CONTRACT.md](docs/API_CONTRACT.md). |
| **What runs in CI** | Default: `pytest … -m "not integration and not open_webui_e2e"` (mocked upstream). Plus Docker **compose smoke**—see [Tests](#tests). |
| **Live / browser** | Opt-in: `AEGISLLM_LIVE_OLLAMA=1` and **`tests/test_integration_live.py`**; Tier C Playwright under **`tests/e2e_open_webui/`** (not default CI). |
| **Known limits** | Same as **What it is not** and the **Out of scope** section in [docs/API_CONTRACT.md](docs/API_CONTRACT.md). |
| **Not a platform** | No quotas, billing, LiteLLM-style provider matrix, or enterprise control plane. |

**This repository** is the integration source of truth: **README**, **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)**, **[docs/SECURITY_POSTURE.md](docs/SECURITY_POSTURE.md)**, and OpenAPI at **`/docs`**.

Before a public alpha tag or announcement, use **[docs/ALPHA_PUBLISH_CHECKLIST.md](docs/ALPHA_PUBLISH_CHECKLIST.md)** (maintainer gate + go/hold criteria).

### Product charter (optional upstream monorepo)

Some teams keep Guard inside a larger **Aegis** repository; wedge docs may live under that repo’s `docs/product/` (not shipped here).

---

## Ollama compatibility

Embeddings require a current Ollama build that implements **`POST /api/embed`** (see [Ollama API — Generate Embeddings](https://github.com/ollama/ollama/blob/main/docs/api.md)). Smoke-tested behavior is expected on **Ollama release-line images** (e.g. `ollama/ollama:latest` at compose time); **pin image tags** if you need reproducibility.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AEGISLLM_BACKEND` | `ollama` | Backend id (only `ollama` implemented today). |
| `AEGISLLM_UPSTREAM_BASE_URL` | _(see below)_ | Ollama API base URL. |
| `AEGISLLM_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | **Legacy** alias for upstream if `AEGISLLM_UPSTREAM_BASE_URL` is unset. |
| `AEGISLLM_LISTEN_HOST` | `127.0.0.1` | Bind address |
| `AEGISLLM_LISTEN_PORT` | `8765` | Bind port |
| `AEGISLLM_API_KEYS` | _(empty)_ | Comma-separated Bearer tokens; if set, required on `/v1/*` routes (not on `/healthz` / `/readyz`). Root and OpenAPI surfaces stay unauthenticated—see **Security / deployment**. |
| `AEGISLLM_CONNECT_TIMEOUT` | `5` | Upstream connect timeout (seconds) |
| `AEGISLLM_READ_TIMEOUT` | `300` | Upstream read timeout (seconds) |
| `AEGISLLM_LOG_LEVEL` | `INFO` | Log level |
| `AEGISLLM_CONFIG` | _(unset)_ | Optional YAML path (see below) |
| `AEGISLLM_LICENSE_KEY` | _(unset)_ | Recorded for future entitlement checks (no enforcement in v0.2) |

Invalid numeric env values fail fast with a clear **configuration error** on startup.

### Optional YAML (`AEGISLLM_CONFIG`)

```yaml
backend: ollama
upstream_base_url: http://127.0.0.1:11434
# Legacy key still accepted:
# ollama_base_url: http://127.0.0.1:11434
listen_host: 0.0.0.0
listen_port: 8765
api_keys: []
timeouts:
  connect: 5.0
  read: 300.0
```

---

## Security / deployment

Typical bind/auth posture (see [docs/API_CONTRACT.md](docs/API_CONTRACT.md) and **[docs/SECURITY_POSTURE.md](docs/SECURITY_POSTURE.md)** for risks, mitigations, and startup logs). **Startup WARNING lines are operator signals** (logging), not automatic lockdown—see SECURITY_POSTURE for what they do and do not enforce.

| Deployment profile | Typical `AEGISLLM_LISTEN_HOST` | API keys | CORS (today) | Public routes | Non-loopback + posture |
|--------------------|-------------------------------|----------|--------------|---------------|-------------------------|
| Local dev | `127.0.0.1` or `::1` (loopback) | Optional | `allow_origins=["*"]` is **fixed in code** (`app.py`), not env-configurable; tighten with a reverse proxy if needed | [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | No **WARNING** logs for auth/CORS on loopback-only binds. |
| LAN / container | Often `0.0.0.0`, `::`, or a LAN IP | **Strongly recommended** | Same as above | Same | With **empty** `AEGISLLM_API_KEYS`, expect **`level=WARNING`** for **unauthenticated `/v1/*`**. Expect a **CORS WARNING** whenever the bind is not loopback-only. |
| Exposed / production | Often `0.0.0.0` or `::` behind LB / published port | **Treat as required**; add firewall / proxy auth / mTLS as appropriate | Same as above | Same | With keys set, the unauthenticated **`/v1/*`** WARNING does **not** fire; the **CORS** WARNING may still fire on non-loopback binds. `/`, `/healthz`, `/readyz`, `/docs`, `/openapi.json`, `/redoc` stay public per the contract—plan network exposure accordingly. |

- **CORS:** The app uses `allow_origins=["*"]` in code; there are **no** CORS-related environment variables. For stricter origins, terminate with a reverse proxy (or fork/configure in code).

- **API keys vs. public routes:** When `AEGISLLM_API_KEYS` is set, Bearer authentication applies to the implemented API routes (e.g. `/v1/*`). These paths remain **unauthenticated** (same set as [docs/API_CONTRACT.md](docs/API_CONTRACT.md)): `/`, `/healthz`, `/readyz`, `/docs`, `/openapi.json`, and `/redoc`. Plan exposure (bind address, firewall, reverse proxy auth) if those surfaces must not be reachable.

- **Upstream base URL:** `AEGISLLM_UPSTREAM_BASE_URL` (and the legacy `AEGISLLM_OLLAMA_BASE_URL` alias) define where the gateway forwards traffic. Treat this as a **trust boundary**: point it only at intended Ollama (or compatible) endpoints. Misconfiguration can make the process relay requests toward arbitrary URLs it can reach (an SSRF-style risk from the Guard host’s perspective).

- **Upstream disclosure:** `GET /v1/models` may include the response header `X-AegisLLM-Upstream-Base`, echoing the configured upstream base URL. Any client that can call this endpoint can observe that value; strip or block the header at a proxy if disclosure is undesirable.

---

## Alternatives to Docker Compose

Use these when Compose is not your primary path.

### Local Python + Ollama on the host (Path B)

Requires **Python 3.10+** and **`ollama serve`** (default upstream `http://127.0.0.1:11434`). Install, run, and the same `curl` checks as Path A: **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** — section **Path B — Local Python … (alternative)**.

### Run the `aegis-llm` CLI (after editable install)

From the clone root, after `pip install -e ".[dev]"` (or `pip install -e .`):

```bash
AEGISLLM_LISTEN_HOST=127.0.0.1 AEGISLLM_LISTEN_PORT=8765 aegis-llm
```

Or: `AEGISLLM_LISTEN_HOST=127.0.0.1 AEGISLLM_LISTEN_PORT=8765 .venv/bin/aegis-llm`

On startup you should see a **structured diagnostics line** (backend, bind URL, upstream, auth, timeouts) and then Uvicorn’s banner. If the bind is **not loopback-only** (`127.0.0.1` / `::1`) and **`AEGISLLM_API_KEYS` is empty**, startup emits a structured **`level=WARNING`** log about **unauthenticated `/v1/*`**. A separate **`level=WARNING`** may log **permissive CORS** for non-loopback binds (even when keys are set). Suppress these by raising `AEGISLLM_LOG_LEVEL` above WARNING, or fix posture—see **[docs/SECURITY_POSTURE.md](docs/SECURITY_POSTURE.md)**.

**Note:** `cd foo && pip install …` only runs `pip` if `cd` succeeds.

### Uvicorn directly

```bash
uvicorn aegis_llm.app:create_app --factory --host 127.0.0.1 --port 8765
```

### Docker (Guard container only)

```bash
docker build -t aegis-llm:local .
docker run --rm -p 8765:8765 \
  -e AEGISLLM_UPSTREAM_BASE_URL=http://host.docker.internal:11434 \
  aegis-llm:local
```

(`AEGISLLM_OLLAMA_BASE_URL` still works as a legacy alias.)

---

## OpenAPI / live schema

`GET /docs` and `/openapi.json` reflect current Pydantic models and routes. For **what is supported vs ignored vs rejected**, stream semantics, and operator-oriented error categories, use **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)**.

---

## Point clients at Guard

After **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**, point tools at Guard using each client’s OpenAI-compatible base URL (often **`http://127.0.0.1:8765/v1`** for SDKs, or **origin only** for some UIs that append `/v1` themselves—see integration doc).

- **Open WebUI:** [docs/INTEGRATION_OPEN_WEBUI.md](docs/INTEGRATION_OPEN_WEBUI.md).

---

## curl examples

With `jq` installed:

```bash
bash examples/curl_examples.sh
```

Override base URL and embedding model name:

```bash
AEGISLLM_EXAMPLE_BASE=http://127.0.0.1:8765 \
AEGISLLM_EXAMPLE_EMBED_MODEL=nomic-embed-text \
bash examples/curl_examples.sh
```

---

## Endpoints

- `GET /healthz` — process up
- `GET /readyz` — upstream reachable (`503` if not)
- `GET /v1/models` — OpenAI-style list (`X-AegisLLM-Backend`, `X-AegisLLM-Upstream-Base`)
- `POST /v1/chat/completions` — chat (stream + non-stream)
- `POST /v1/embeddings` — embeddings (Ollama `/api/embed`)

---

## Tests

- **Default (CI + local gate):** mocked upstream, no Docker, no live Ollama, no Tier C browser tests—the same filter GitHub Actions uses:

  ```bash
  pytest tests/ -q -m "not integration and not open_webui_e2e"
  ```

  **Passing** here means the **bounded** contract in [docs/API_CONTRACT.md](docs/API_CONTRACT.md) matches the implementation for the routes under test—it does **not** mean every OpenAI client or feature works.

- **Integration (opt-in):** set **`AEGISLLM_LIVE_OLLAMA=1`** and run `pytest tests/ -q -m "not open_webui_e2e"` to include **`tests/test_integration_live.py`** (real Ollama and/or Guard). Optional env: **`AEGISLLM_GUARD_BASE_URL`**, **`AEGISLLM_UPSTREAM_BASE_URL`**, **`AEGISLLM_LIVE_BEARER`**, **`AEGISLLM_LIVE_EMBED_MODEL`**—see each test’s docstring.

- **Tier C (optional):** Open WebUI + Playwright: `docker compose --profile tier-c up`, then `pip install -e ".[e2e]"`, `python -m playwright install`, `AEGISLLM_OPEN_WEBUI_E2E=1 pytest tests/e2e_open_webui/ -q`. Details: [`tests/e2e_open_webui/README.md`](tests/e2e_open_webui/README.md).

- **Compose smoke:** `bash scripts/smoke_compose.sh` (Docker; exercises `docker-compose.yml`).

GitHub Actions (see [`.github/workflows/aegis-llm.yml`](.github/workflows/aegis-llm.yml)) runs the **default pytest** command on **Python 3.10 / 3.12 / 3.13** and a **`compose-smoke`** job.

---

## License

Licensed under the **Apache License 2.0**. See the [`LICENSE`](LICENSE) file in the repository root for the full text and copyright notice.

The **product** positioning above (alpha, bounded API, Ollama-first) is intentionally narrow—see [Alpha release scope](#alpha-release-scope).
