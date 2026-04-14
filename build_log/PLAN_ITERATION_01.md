# Plan: Iteration 1 — Declared API contract

**Parent:** [ITERATIONS.md](./ITERATIONS.md) · **Iteration 1**  
**Goal:** Move from “directionally OpenAI-compatible” to **compatibility with explicit, reviewable boundaries**—without adding endpoints or features.

**Wording note:** “Reviewable” means humans and integrators can verify claims against this doc and the cited code paths. It does **not** promise machine-enforced contract tests unless we add those later; avoid implying formal verification we do not ship.

---

## 1. Objective

A new integrator (or security reviewer) can answer in **one place**:

| Question | Answer source |
|----------|----------------|
| Which HTTP routes exist and what do they return? | Contract doc + README pointer |
| For each request field: **rejected**, **accepted but ignored**, **accepted and forwarded**, or **accepted with mediated effect**? | Tables + `schemas.py` |
| What is intentionally **not** supported? | Grouped “Out of scope” sections |
| Which upstream backend is real in production today? | Single row: **Ollama only** |
| Where does behavior differ from OpenAI (approximations)? | Normalization / translation notes |

**Non-goal:** Implementing new API surface to “complete” OpenAI parity.

---

## 2. Code truth baseline (audit before writing)

Use these as the source of truth when drafting tables; update the doc if code changes.

| Area | Location |
|------|----------|
| Chat request fields | `aegis_llm/schemas.py` — `ChatCompletionRequest`, `ChatMessage` |
| Embeddings request | `aegis_llm/schemas.py` — `EmbeddingsRequest` |
| Routes | `aegis_llm/routes/openai.py`, `aegis_llm/routes/health.py`, `aegis_llm/app.py` (`/`) |
| Models list extras | `aegis_llm/backends/ollama.py` — `x_ollama` keys |
| Error shapes | `aegis_llm/errors.py`, route handlers |
| Auth scope | `aegis_llm/middleware/auth.py` — `_public_path` |

**Already documented in README (v0.2):** high-level compatibility scope, embeddings → `/api/embed`, security section. Iteration 1 **centralizes and tabulates** this so README can stay a short index.

---

## 3. Deliverables

### 3.1 New doc: `docs/API_CONTRACT.md`

Single canonical contract (Markdown). Suggested section order:

#### 1. Compatibility philosophy (Interpretation)

Short spine at the top—**3–5 bullets**, for example:

- This document defines the **supported subset** of OpenAI-shaped usage; it is the canonical compatibility statement for integrators.
- Generated **OpenAPI** at `/docs` is **descriptive** (what the server exposes today), not the canonical boundary for “what we promise.”
- Behavior **not described here** should not be relied on.
- Unsupported fields may be **rejected** (validation error), **ignored** (silent drop), or **accepted without semantic effect**—each must be stated per area below, not lumped as “accepted.”
- **Production backend support today is Ollama only.**

#### 2. Purpose (brief)

One tight paragraph: bounded spec; update this file when behavior changes intentionally; link to package version.

#### 3. Backends (production reality)

- Row: **Ollama** — supported.  
- **Other `AEGISLLM_BACKEND` values:** not supported / factory is internal.  
- One sentence: abstraction exists for structure and tests, not a multi-backend product claim.

#### 4. HTTP surface

Table: method, path, auth (if keys configured), success shape, notable headers, typical status codes.

#### 5. `GET /v1/models`

- Response shape (`object`, `data[]`, per-item fields).  
- Optional `x_ollama` — informational, not portable.  
- Headers: `X-AegisLLM-Backend`, `X-AegisLLM-Upstream-Base` (disclosure note).

#### 6. `POST /v1/chat/completions`

- **Request fields table (critical):** use explicit columns so “accepted” is not ambiguous, e.g.:

  | Field | Request handling | Upstream / effect |
  |-------|------------------|-------------------|
  | *(per field)* | **rejected** (400 + type) / **ignored** (not in schema or `extra="ignore"`) / **validated** | **forwarded** to Ollama / **transformed** (describe) / **no-op** at upstream |

  If a field validates but does **not** meaningfully change Ollama behavior, say so explicitly (“validated, forwarded; Ollama may ignore or interpret per its own rules”)—do not blur **“parses OK”** with **“drives upstream.”**

- **Messages:** `role`, `content` as string or list of parts; which part shapes are **mapped** (e.g. `type: text`) vs **dropped** vs **cause rejection**.

- **Normalization / translation notes** (short subsection):  
  - What is **transformed** before forwarding (e.g. message content flattening).  
  - What is **approximated** on the response (e.g. `finish_reason`, usage, stream deltas).  
  - What is **passthrough** where Ollama and OpenAI shapes align.

- **Streaming:** SSE framing, `data: [DONE]`, error termination pattern (reference tests).  
- **Non-stream:** document `finish_reason` and any static choices as **approximation**, not OpenAI parity.  
- **Not supported** (pointer to Out of scope): tools, function calling, logprobs, `n>1`, non-text modalities as product claims, Responses API.

#### 7. `POST /v1/embeddings`

- Same discipline: table for `model`, `input`, `encoding_format`, `dimensions`, `truncate` with **rejected / forwarded / transformed** as applicable.  
- **Normalization / translation notes:** e.g. batch `input` → Ollama body; response mapping to OpenAI-style `data[]` and `usage`.  
- Upstream: Ollama `POST /api/embed`.  
- Rejected: `base64`, empty `input` list, empty strings (per `schemas.py`).

#### 8. Health

- `GET /healthz`, `GET /readyz` — bodies and status codes.

#### 9. Errors

Keep a **single** client-visible error object shape, but **categorize** for operators (separate sub-bullets or small table):

| Category | Examples | Typical HTTP / `error.type` |
|----------|----------|-----------------------------|
| **Transport** | timeouts, connection refused | 504 / 502, `timeout` / `connection_error` |
| **Validation** | Pydantic body errors | 400, `invalid_request_error` |
| **Auth** | missing/wrong/malformed Bearer | 401 / 403, `authentication_error` |
| **Upstream protocol / semantics** | HTTP error from Ollama, invalid JSON body, stream failures | 502 / SSE error event, `upstream_http_error` / `upstream_error` / etc. |

Note: categories can overlap in implementation; the point is **clarity for operators**, not new error types in this iteration.

#### 10. Out of scope (explicit, grouped)

Avoid a flat “bullet graveyard.” Use **three groups**:

1. **Unimplemented OpenAI API families** (e.g. images, audio, batches, assistants, fine-tunes, moderations, realtime—only list what is relevant to client expectations).  
2. **Unimplemented or non-portable chat semantics** (tools, parallel completions, modalities, etc.).  
3. **Unsupported product / backend claims** (multi-backend routing, quotas, full OpenAI parity).

#### 11. Versioning and review footer

- Reference `aegis_llm.version.__version__` (or README product line).  
- **Footer:** `Last reviewed against aegis-llm vX.Y.Z / commit / date` (pick one convention and stick to it). Update when behavior or schema changes.

### 3.2 README adjustments (minimal)

- Add a prominent link near the top or after the charter: **“Canonical API boundaries: [docs/API_CONTRACT.md](docs/API_CONTRACT.md).”**
- Shorten or **dedupe** the long “OpenAPI / compatibility scope” bullet list if it repeats the new doc—README should **summarize** and point to the contract file.
- Keep **Security / deployment** in README (operational); cross-link from contract only if one line helps.

### 3.3 Monorepo product spec (optional, same iteration)

- If `docs/product/LOCAL_LLM_SERVING_PLATFORM_SPEC.md` still describes Guard only in prose, add **one short subsection or bullet**: “Bounded OpenAI subset documented in `zed_toolkit/services/aegis_llm/docs/API_CONTRACT.md`.”  
- **Do not** inflate platform claims; this is a pointer for auditors.

### 3.4 Tests and review (lightweight)

- **No new routes** in this iteration.  
- Optional: extend OpenAPI path smoke tests if useful (already partially covered by `test_openai_contract.py`).  
- **Do not** add CI that only asserts `API_CONTRACT.md` exists—existence is trivial; **accuracy** matters. Track contract updates via **human review** or a **PR checklist** (e.g. “If you changed `schemas.py` or route behavior, update `API_CONTRACT.md` and the review footer.”).

---

## 4. Execution order

| Step | Task | Output |
|------|------|--------|
| 1 | Re-read `schemas.py`, `openai.py`, `ollama.py`, `errors.py`, `auth.py` | Notes of any README/contract drift |
| 2 | Draft `docs/API_CONTRACT.md` (philosophy → tables → normalization notes → grouped out of scope → footer) | First complete draft |
| 3 | Trim README compatibility section; add link to contract | README PR chunk |
| 4 | (Optional) Touch monorepo `LOCAL_LLM_SERVING_PLATFORM_SPEC.md` | Single pointer |
| 5 | Self-review: every **forwarded / ignored / rejected** row traceable to code or test | Checklist ✓ |
| 6 | Commit: **docs-only** preferred (`docs/API_CONTRACT.md` + README ± spec)—fits “per logical change” commit habit | One or two commits |

---

## 5. Acceptance checklist (Iteration 1 done when)

- [ ] `docs/API_CONTRACT.md` exists and is linked from README.  
- [ ] **Compatibility philosophy** (Interpretation) section at top with OpenAPI vs canonical boundary called out.  
- [ ] **Supported vs unsupported** is explicit; no implied full OpenAI parity.  
- [ ] **Ollama-only** production backend is stated clearly (philosophy + backends section).  
- [ ] Chat and embeddings use **rejected / ignored / forwarded / mediated** language consistently; **normalization / translation** subsections present.  
- [ ] Streaming and non-stream chat described; known **approximations** named.  
- [ ] **Errors** section separates transport, validation, auth, upstream (for operators).  
- [ ] **Out of scope** is grouped (API families / chat semantics / product claims), not only a flat list.  
- [ ] **Last reviewed** footer in contract doc.  
- [ ] Embeddings limits (`encoding_format`, empty `input`) match `schemas.py`.  
- [ ] No new API routes added in this iteration.  
- [ ] No low-value “file exists” CI check; review discipline preferred.

---

## 6. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Doc drifts from code | Source of truth in §2; **footer** with version / date; PR checklist when touching schemas or routes |
| README becomes too long | Prefer linking; README = onboard + ops |
| Over-specifying future behavior | Document **current** behavior only; use “not implemented” liberally |
| Overclaiming “checkable” | Use **reviewable** in goals; machine checks only if/when added |

---

## 7. Handoff to Iteration 2

After this iteration, **Iteration 2** (deployment warnings) can cite `API_CONTRACT.md` for “what we expose” while startup warnings focus on **how** it is exposed (bind + auth + CORS).

---

## 8. Review notes (incorporated)

Feedback applied in this plan revision:

- **Reviewable** vs machine-checkable wording.  
- Chat/embeddings: **accepted vs forwarded vs ignored vs rejected** made a first-class table requirement.  
- **Normalization / translation** subsections for mediated compatibility.  
- **Error categories** for operators.  
- **Grouped out of scope.**  
- **Compatibility philosophy** block at top of `API_CONTRACT.md`.  
- **Last reviewed** footer required.  
- **Removed** recommendation for trivial doc-existence CI in favor of human / PR checklist.
