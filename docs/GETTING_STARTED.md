# Getting started — AegisLLM Guard

Step-by-step from **nothing running** to **first successful chat** through Guard. After this, point any **OpenAI-compatible** client at Guard’s base URL (see [INTEGRATION_OPEN_WEBUI.md](./INTEGRATION_OPEN_WEBUI.md) for Open WebUI).

**Canonical first run:** use **Path A (Docker Compose)** below unless you already run Ollama on the host and prefer a local Python venv—the [README](../README.md) quickstart points here for Path A.

**Time:** about 10–20 minutes, mostly model download on first run.

---

## What you will have at the end

- **Guard** listening on **port 8765** (default), forwarding to **Ollama**.
- Confirmed **`/healthz`**, **`/readyz`**, and **`/v1/models`**.
- One **`POST /v1/chat/completions`** that returns an assistant reply (non-streaming).

---

## Prerequisites

- **Path A:** **Docker** and **Docker Compose** (see below).
- **Path B (alternative):** Python **3.10+** and **`ollama serve`** on the same machine.
- **Optional:** `curl` and `jq` for copy-paste checks (`jq` is optional if you read raw JSON).

Working directory for commands is the **repository root** (the folder that contains `docker-compose.yml` and `pyproject.toml`).

---

## Path A — Docker Compose (recommended first run)

Brings up **Ollama + Guard** on one network. This is the **primary** quickstart path for new users (matches the [README](../README.md) canonical quickstart).

### 1. Start the stack

```bash
docker compose up --build
```

Leave this terminal open until you are done testing, or add `-d` to run detached.

### 2. Pull at least one chat model

In **another** terminal:

```bash
docker compose exec ollama ollama pull llama3.2
```

Use any tag you prefer; the examples below assume **`llama3.2`**. If you pull a different name, substitute it in the JSON `model` field.

*(Optional, for embeddings checks later: `docker compose exec ollama ollama pull nomic-embed-text`.)*

### 3. Check Guard and upstream

```bash
curl -sS http://127.0.0.1:8765/healthz
curl -sS http://127.0.0.1:8765/readyz
curl -sS http://127.0.0.1:8765/v1/models
```

Expect:

- **`/healthz`:** `{"status":"ok"}` (or equivalent JSON).
- **`/readyz`:** `status` of `ready` when Ollama is reachable from Guard (may be `not_ready` briefly while Ollama starts).
- **`/v1/models`:** JSON with `object` = `list` and a non-empty `data` array after pulls succeed.

With `jq`:

```bash
curl -sS http://127.0.0.1:8765/readyz | jq .
curl -sS http://127.0.0.1:8765/v1/models | jq '.data[].id'
```

### 4. First chat (non-stream)

```bash
curl -sS http://127.0.0.1:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2","messages":[{"role":"user","content":"Say hello in one short sentence."}],"stream":false}'
```

You should get **`200`** JSON with `choices[0].message.content` populated.

### 5. (Optional) See streaming on the wire

```bash
curl -sN http://127.0.0.1:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2","messages":[{"role":"user","content":"Count from 1 to 3 slowly."}],"stream":true}'
```

Expect **`text/event-stream`**, multiple `data:` lines, and a final **`[DONE]`** line. Press Ctrl+C when finished reading.

### 6. Scripted examples (optional)

From the same service directory:

```bash
bash examples/curl_examples.sh
```

Uses `http://127.0.0.1:8765` by default; override with `AEGISLLM_EXAMPLE_BASE=...` if Guard listens elsewhere.

---

## Path B — Local Python + Ollama already on the host (alternative)

Use **Path B** when you already run **`ollama serve`** on the machine (default **`http://127.0.0.1:11434`**) and want Guard in a **venv** without Compose—not the default first-run path.

### 1. Install Guard (editable, dev extras)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Run Guard

```bash
AEGISLLM_LISTEN_HOST=127.0.0.1 AEGISLLM_LISTEN_PORT=8765 aegis-llm
```

If Ollama is **not** on the default URL:

```bash
export AEGISLLM_UPSTREAM_BASE_URL=http://127.0.0.1:11434
AEGISLLM_LISTEN_HOST=127.0.0.1 AEGISLLM_LISTEN_PORT=8765 aegis-llm
```

### 3. Pull a model (host Ollama)

```bash
ollama pull llama3.2
```

### 4. Same checks as Path A (steps 3–5)

Use `http://127.0.0.1:8765` as the base URL for `curl`.

---

## Point a UI or SDK at Guard

| Client | What to do |
|--------|----------------|
| **Open WebUI** | Follow [INTEGRATION_OPEN_WEBUI.md](./INTEGRATION_OPEN_WEBUI.md) (base URL, model list, stream checklist). Optional compose profile: `docker compose --profile tier-c up` for Open WebUI in the same stack. |
| **OpenAI Python SDK** | `base_url` = `http://127.0.0.1:8765/v1` (include **`/v1`** for the SDK). Do **not** put `/v1` in `AEGISLLM_GUARD_BASE_URL` env vars used elsewhere—see integration doc. |

**Contract reference:** supported fields, streaming semantics, and errors are in [API_CONTRACT.md](./API_CONTRACT.md).

---

## API keys (optional)

If you set **`AEGISLLM_API_KEYS`** (comma-separated), clients must send **`Authorization: Bearer <key>`** on **`/v1/*`**. **`/healthz`** and **`/readyz`** stay unauthenticated by default. See the service [README.md](../README.md) **Security / deployment** table and [SECURITY_POSTURE.md](./SECURITY_POSTURE.md).

---

## If something fails

| Symptom | Check |
|---------|--------|
| **`/readyz` not ready** | Ollama up? Correct `AEGISLLM_UPSTREAM_BASE_URL`? From inside Guard container, can it reach `http://ollama:11434` (compose) or your host URL? |
| **Empty `v1/models`** | Run `docker compose exec ollama ollama list` (or host `ollama list`) and pull a model. |
| **Chat `502` / upstream errors** | Model name spelling; Ollama logs; Guard logs. |
| **Validation `400`** | Body matches [API_CONTRACT.md](./API_CONTRACT.md); unknown top-level keys on **`/v1/embeddings`** are rejected (`extra=forbid`). |

---

## Feedback and adoption

- **Product / wedge framing:** may exist in a parent **Aegis** monorepo under `docs/product/`; not bundled here.
- **Behavior truth:** [API_CONTRACT.md](./API_CONTRACT.md), [SECURITY_POSTURE.md](./SECURITY_POSTURE.md), and tests under `tests/`.

If you are trying Guard for a real integration, note **what client you used**, **Guard + Ollama versions or image tags**, and **what broke or surprised you**—that is the highest-signal feedback at this stage.
