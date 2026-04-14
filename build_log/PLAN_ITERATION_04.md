# Plan: Iteration 4 — Schema and validation discipline

**Parent:** [ITERATIONS.md](./ITERATIONS.md) · **Iteration 4**  
**Goal:** Public contract feels **intentional**: unknown fields fail **predictably** (stable 4xx shape) where safe—not accidentally permissive via `extra="ignore"` everywhere.

**Depends on:** Iteration 3 streaming behavior and docs stable enough to re-run a **short** stream smoke after tightening ([PLAN_ITERATION_03.md](./PLAN_ITERATION_03.md) §8 handoff).

**Explicit non-goal:** Breaking common clients (Open WebUI, OpenAI Python SDK) to chase theoretical purity; universal OpenAI field coverage.

---

## 0. Summary

| Phase | Focus | Primary artifacts |
|-------|--------|-------------------|
| **04A** | Audit + risk map | This file § “04A findings”; `build_log/AUDIT_ITERATION_04_SCHEMA.md` |
| **04B** | Pydantic + route errors | `aegis_llm/schemas.py`, `routes/openai.py` (or shared exception handler) |
| **04C** | Contract + tests | `docs/API_CONTRACT.md`, `tests/test_chat.py` / new focused tests |

---

## 1. Objective

- **Before:** `ChatCompletionRequest`, `ChatMessage`, `EmbeddingsRequest` use `extra="ignore"`; contract documents that unknown keys are dropped without error.
- **After (incremental):** Selected models use `extra="forbid"` **or** explicit allow-list with clear `invalid_request_error` messages; contract matches code; Tier A tests prove behavior.

---

## 2. Execution order

1. **04A** — Inventory all request `BaseModel`s, FastAPI validation error handling, and repo-wide JSON bodies that include non-schema keys (tests, smoke, docs examples). Classify **safe to forbid** vs **likely sent by real clients** (defer).
2. **04B** — Apply smallest Pydantic change with tests green; add/align **422/400** JSON error shape if FastAPI default is insufficient.
3. **04C** — Patch `API_CONTRACT.md` tables (“ignored” → “rejected” where true); add regression tests for one happy + one unknown-field path.

---

## 3. Done when (Iteration 4)

- [x] At least one hot-path request model uses **`extra="forbid"`** (or documented equivalent) without breaking scoped client checks. *(Embeddings only as of 04B/04C; chat still `ignore`.)*
- [x] Unknown-field responses use a **stable** `error.type` / `message` pattern documented in contract. *(Existing `RequestValidationError` → 400 `invalid_request_error`; embeddings unknown keys now use this path.)*
- [x] `docs/API_CONTRACT.md` matches implementation. *(Embeddings table + intro; chat rows unchanged.)*
- [ ] Stream smoke (Tier A + quick manual or Tier B if available) still passes after merge.

**04B/04C status (2026-04-11):** Completed for **embeddings only** (`EmbeddingsRequest` → `forbid`, `tests/test_embeddings.py`, `docs/API_CONTRACT.md`). Chat `extra` policy unchanged pending payload classification. **Scenario map:** [SCENARIO_COVERAGE.md](./SCENARIO_COVERAGE.md) embeddings row lists `test_embeddings_rejects_unknown_top_level_key` and contract pointer.

---

## 4. Risks

| Risk | Mitigation |
|------|------------|
| Open WebUI sends benign extra keys | Grep OWUI / capture real payloads before forbid on chat |
| SDK sends `user`, `seed`, etc. | Cross-check OpenAI SDK default payload fields |
| Silent CI break | Add tests before flipping `ignore` → `forbid` |

---

## 5. Subagent brief (04A — in flight)

**Task:** Read-only audit + first recommendation only unless coordinator promotes implementation in the same PR.

**Paths:** `aegis_llm/schemas.py`, `aegis_llm/routes/openai.py`, `tests/test_*.py`, `scripts/smoke_compose.sh`, `docs/API_CONTRACT.md` (chat + embeddings request tables).

**Deliver back:** (1) model/table of current `extra` policy (2) list of extra keys appearing in tests or smoke (3) recommended **first** model to tighten (with rationale) (4) any FastAPI `RequestValidationError` handler gap.

---

## 04A findings (2026-04-13)

- **Inventory:** Only `ChatMessage`, `ChatCompletionRequest`, and `EmbeddingsRequest` in `aegis_llm/schemas.py`. Chat models use `extra="ignore"`; **`EmbeddingsRequest` is `extra="forbid"`** since 04B/04C. No other `BaseModel` body schemas under `routes/`.
- **Validation errors:** `RequestValidationError` is handled in `aegis_llm/app.py` (`create_app`), not `main.py` — **400** + `invalid_request_error` via `error_payload`; no handler gap for body validation.
- **Tests / smoke:** No `POST /v1/chat/completions` or `/v1/embeddings` fixtures in `tests/` or `scripts/` were found with **undocumented top-level** JSON keys; tightening can still break external OpenAI-shaped clients (see defer list in audit).
- **Contract:** `docs/API_CONTRACT.md` must be updated in 04C when any model flips to forbid (tables currently say unknown keys are ignored).
- **Full write-up:** [AUDIT_ITERATION_04_SCHEMA.md](./AUDIT_ITERATION_04_SCHEMA.md) (models table, defer list, first-step recommendation).
