# AegisLLM Guard

**What this is (v0.2):** an **OpenAI-compatible reliability gateway for Ollama**—a thin layer clients talk to as if it were an OpenAI HTTP API, while **Ollama stays the engine** you already run. It is not a universal local LLM platform, not a full OpenAI API mirror, and **production is Ollama-only** (an internal `Backend` protocol exists for structure and tests, not for “pick another vendor” today).

It adds predictable **timeouts**, **health/readiness** (`/healthz`, `/readyz`), optional **API keys**, **request IDs**, **typed request validation** for the implemented subset, **consistent error shapes**, **structured access logs**, and **`/v1/embeddings`** (mapped to Ollama **`POST /api/embed`**) so chat UIs and RAG stacks **fail fast with clear errors** instead of hanging on a stuck upstream.

### What problem it addresses

- **Hung or vague failures** when Open WebUI, SDKs, or agents call Ollama over raw HTTP and the upstream misbehaves or disappears mid-request.
- **“OpenAI-compatible” confusion** where clients assume fields or semantics you do not actually support—Guard documents a **bounded** subset in the contract and validates requests accordingly.
- **Operator blind spots:** readiness vs liveness split, startup warnings for risky bind/auth combinations, and logs you can grep without spelunking Ollama internals.

### Why it is an easy adoption choice

- **No model migration:** you keep the same Ollama models and pulls; Guard only changes **where clients point** (`http://<guard>:8765` with `/v1/...` paths).
- **Small surface:** one process (or one container next to Ollama in Compose), env-driven config, **Docker Compose** path from zero to first chat in minutes—see **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**.
- **Honest boundaries:** if something is unsupported, the goal is a **predictable** `4xx` / error payload, not silent weirdness—see the contract below.

**What it is not yet:** multi-backend routing, quotas, tool calling, `encoding_format: base64` for embeddings, or broad drop-in compatibility with every OpenAI client feature.

**Canonical API boundaries (supported subset, rejected vs ignored fields, errors):** [docs/API_CONTRACT.md](docs/API_CONTRACT.md). OpenAPI at `/docs` is descriptive; the contract doc is the integration source of truth.

### Quick start (step by step)

**[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** — Docker Compose or local Python, pull a model, verify health/models, first `curl` chat, optional stream, then link out to Open WebUI / SDK notes.

## Ollama compatibility

Embeddings require a current Ollama build that implements **`POST /api/embed`** (see [Ollama API — Generate Embeddings](https://github.com/ollama/ollama/blob/main/docs/api.md)). Smoke-tested behavior is expected on **Ollama release-line images** (e.g. `ollama/ollama:latest` at compose time); pin versions in production if you need reproducibility.

## Product charter (optional upstream monorepo)

Some teams keep Guard inside a larger **Aegis** repository; product charter or wedge docs may live under that repo’s `docs/product/` (not shipped in this standalone tree).

**This repository** is the integration source of truth: **README**, **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)**, **[docs/SECURITY_POSTURE.md](docs/SECURITY_POSTURE.md)**, and OpenAPI at **`/docs`**.

## Requirements

- Python 3.10+
- A running [Ollama](https://ollama.com/) server (default `http://127.0.0.1:11434`)

## Install (development)

From the **clone root** of this repository (the directory that contains `pyproject.toml`):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

If Guard is **vendored inside a larger monorepo**, `cd` into this package directory (the folder that contains this `README.md`) first, then run the same commands.

## Run

From the same directory:

```bash
AEGISLLM_LISTEN_HOST=127.0.0.1 AEGISLLM_LISTEN_PORT=8765 aegis-llm
```

Or without activating the venv:

```bash
AEGISLLM_LISTEN_HOST=127.0.0.1 AEGISLLM_LISTEN_PORT=8765 .venv/bin/aegis-llm
```

On startup you should see a **structured diagnostics line** (backend, bind URL, upstream, auth, timeouts) and then Uvicorn’s banner. If the bind is **not loopback-only** (`127.0.0.1` / `::1`) and **`AEGISLLM_API_KEYS` is empty**, startup emits a structured **`level=WARNING`** log about **unauthenticated `/v1/*`**. A separate **`level=WARNING`** may log **permissive CORS** for non-loopback binds (even when keys are set). Suppress these by raising `AEGISLLM_LOG_LEVEL` above WARNING, or fix posture—see **[docs/SECURITY_POSTURE.md](docs/SECURITY_POSTURE.md)** and **Security / deployment** below.

**Note:** `cd foo && pip install …` only runs `pip` if `cd` succeeds.

### Uvicorn directly

```bash
uvicorn aegis_llm.app:create_app --factory --host 127.0.0.1 --port 8765
```

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

## Security / deployment

Typical bind/auth posture (see [docs/API_CONTRACT.md](docs/API_CONTRACT.md) and **[docs/SECURITY_POSTURE.md](docs/SECURITY_POSTURE.md)** for risks, mitigations, and startup logs):

| Deployment profile | Typical `AEGISLLM_LISTEN_HOST` | API keys | CORS (today) | Public routes | Non-loopback + posture |
|--------------------|-------------------------------|----------|--------------|---------------|-------------------------|
| Local dev | `127.0.0.1` or `::1` (loopback) | Optional | `allow_origins=["*"]` is **fixed in code** (`app.py`), not env-configurable; tighten with a reverse proxy if needed | [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | No **WARNING** logs for auth/CORS on loopback-only binds. |
| LAN / container | Often `0.0.0.0`, `::`, or a LAN IP | **Strongly recommended** | Same as above | Same | With **empty** `AEGISLLM_API_KEYS`, expect **`level=WARNING`** for **unauthenticated `/v1/*`**. Expect a **CORS WARNING** whenever the bind is not loopback-only. |
| Exposed / production | Often `0.0.0.0` or `::` behind LB / published port | **Treat as required**; add firewall / proxy auth / mTLS as appropriate | Same as above | Same | With keys set, the unauthenticated **`/v1/*`** WARNING does **not** fire; the **CORS** WARNING may still fire on non-loopback binds. `/`, `/healthz`, `/readyz`, `/docs`, `/openapi.json`, `/redoc` stay public per the contract—plan network exposure accordingly. |

- **CORS:** The app uses `allow_origins=["*"]` in code; there are **no** CORS-related environment variables. For stricter origins, terminate with a reverse proxy (or fork/configure in code).

- **API keys vs. public routes:** When `AEGISLLM_API_KEYS` is set, Bearer authentication applies to the implemented API routes (e.g. `/v1/*`). These paths remain **unauthenticated** (same set as [docs/API_CONTRACT.md](docs/API_CONTRACT.md)): `/`, `/healthz`, `/readyz`, `/docs`, `/openapi.json`, and `/redoc`. Plan exposure (bind address, firewall, reverse proxy auth) if those surfaces must not be reachable.

- **Upstream base URL:** `AEGISLLM_UPSTREAM_BASE_URL` (and the legacy `AEGISLLM_OLLAMA_BASE_URL` alias) define where the gateway forwards traffic. Treat this as a **trust boundary**: point it only at intended Ollama (or compatible) endpoints. Misconfiguration can make the process relay requests toward arbitrary URLs it can reach (an SSRF-style risk from the Guard host’s perspective).

- **Upstream disclosure:** `GET /v1/models` may include the response header `X-AegisLLM-Upstream-Base`, echoing the configured upstream base URL. Any client that can call this endpoint can observe that value; strip or block the header at a proxy if disclosure is undesirable.

## OpenAPI / live schema

`GET /docs` and `/openapi.json` reflect current Pydantic models and routes. For **what is supported vs ignored vs rejected**, stream semantics, and operator-oriented error categories, use **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)**.

## Point clients at Guard

After **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**, point tools at Guard using each client’s OpenAI-compatible base URL (often **`http://127.0.0.1:8765/v1`** for SDKs, or **origin only** for some UIs that append `/v1` themselves—see integration doc).

- **Open WebUI:** checklist and streaming verification in [docs/INTEGRATION_OPEN_WEBUI.md](docs/INTEGRATION_OPEN_WEBUI.md).

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

## Endpoints

- `GET /healthz` — process up
- `GET /readyz` — upstream reachable (`503` if not)
- `GET /v1/models` — OpenAI-style list (`X-AegisLLM-Backend`, `X-AegisLLM-Upstream-Base`)
- `POST /v1/chat/completions` — chat (stream + non-stream)
- `POST /v1/embeddings` — embeddings (Ollama `/api/embed`)

## Docker (Guard only)

```bash
docker build -t aegis-llm:local .
docker run --rm -p 8765:8765 \
  -e AEGISLLM_UPSTREAM_BASE_URL=http://host.docker.internal:11434 \
  aegis-llm:local
```

(`AEGISLLM_OLLAMA_BASE_URL` still works as a legacy alias.)

## Docker Compose (Ollama + Guard)

From the repository root:

```bash
docker compose up --build
```

Guard on **localhost:8765**, Ollama on **localhost:11434**. Pull models inside the stack, e.g.:

```bash
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull nomic-embed-text
```

## Tests

Default (mocked upstream, no Docker, same filter as PR CI):

```bash
pytest tests/ -q -m "not integration and not open_webui_e2e"
```

To include **integration** live tests (still excluding Tier C browser tests):

```bash
pytest tests/ -q -m "not open_webui_e2e"
```

**Live checks** (real Ollama and optionally a running Guard process): set **`AEGISLLM_LIVE_OLLAMA=1`**, then run `pytest tests/ -m "not open_webui_e2e"` including **`tests/test_integration_live.py`**. Optional env: **`AEGISLLM_GUARD_BASE_URL`** (default `http://127.0.0.1:8765`), **`AEGISLLM_UPSTREAM_BASE_URL`** for direct Ollama probes (default `http://127.0.0.1:11434`). Use **`Authorization: Bearer …`** when Guard is configured with **`AEGISLLM_API_KEYS`** (see each test’s docstring).

**Tier C (Open WebUI + Playwright):** `docker compose --profile tier-c up`, then `pip install -e ".[e2e]"`, `python -m playwright install`, `AEGISLLM_OPEN_WEBUI_E2E=1 pytest tests/e2e_open_webui/ -q`. Details: [`tests/e2e_open_webui/README.md`](tests/e2e_open_webui/README.md).

**Compose smoke** (builds and exercises the stack from `docker-compose.yml`):

```bash
bash scripts/smoke_compose.sh
```

GitHub Actions (see [`.github/workflows/aegis-llm.yml`](.github/workflows/aegis-llm.yml)) runs **`pytest -m "not integration and not open_webui_e2e"`** on **Python 3.10 / 3.12 / 3.13** and a **`compose-smoke`** job that executes **`scripts/smoke_compose.sh`** (Docker required).

## License

Proprietary (Aegis Research Team). Enterprise use and redistribution are governed separately from this README.
