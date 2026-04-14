# Sub-plan 03E — Backpressure review (post 03A–D)

**Parent:** [PLAN_ITERATION_03.md](./PLAN_ITERATION_03.md)  
**Agent role:** **Read-only / advisory** reviewer of prior sub-plan outputs and tight coupling to code tests. **Does not** implement fixes unless the coordinator explicitly promotes items to a new execution pass.

**Depends on:** [03A](./PLAN_ITERATION_03A_INTEGRATION.md)–[03D](./PLAN_ITERATION_03D_SCENARIO_README.md) merged (integration doc, contract, scenario map, README).  
**Blocks:** nothing.

**Primary deliverable:** [`REVIEW_ITERATION_03_BACKPRESSURE.md`](./REVIEW_ITERATION_03_BACKPRESSURE.md) (findings + severities). Optional: short PR comment or coordinator checklist.

---

## Objective

Apply **backpressure**: catch **DRY** drift, **KISS** bloat, **integration-test holes**, and **reasonable edge cases** before Iteration 3 is signed off—without turning the review into a second implementation track.

---

## Scope (read these)

| Area | Paths |
|------|--------|
| Prior agent docs | `docs/INTEGRATION_OPEN_WEBUI.md`, `docs/API_CONTRACT.md` (streaming + neighbors), `build_log/SCENARIO_COVERAGE.md`, `README.md` (Open WebUI line) |
| Parent / sub-plans | `build_log/PLAN_ITERATION_03.md`, `PLAN_ITERATION_03A`–`03D` |
| Streaming code + tests | `aegis_llm/routes/openai.py`, `aegis_llm/backends/ollama.py`, `aegis_llm/errors.py`; `tests/test_chat.py`, `tests/test_hardening.py` (stream paths) |

---

## Review dimensions

### 1. DRY (Don’t Repeat Yourself)

- Same **§1** criteria or prose repeated across parent plan, integration doc, and contract without a **single canonical** pointer where one sentence would do.
- **Functional checklist** vs **Streaming verification**: overlap on “stream chat” without cross-reference.
- Contract **Operational verification** vs integration **Status** paragraph: necessary duplication vs merge opportunity.

### 2. KISS (Keep It Simple)

- Checklists: minimum viable rows vs operator fatigue.
- SDK snippet: smallest correct example; avoid env var combinations that confuse (`base_url` + `/v1` rules).
- Scenario table cell length: still scannable?

### 3. Integration testing holes

- What **03A** claims manually vs what **pytest** covers (mocked upstream only).
- Gaps in `SCENARIO_COVERAGE.md` **Gaps** table vs current streaming story.
- Auth + stream, stream + upstream timeout mid-chunk, invalid NDJSON mid-stream (partially covered)—note **only**; do not expand scope into full matrix.

### 4. Reasonable edge cases (document or code)

- `base_url` construction (double `/v1`, trailing slash).
- Open WebUI base URL with vs without `/v1` (already mentioned—consistent with Connection settings?).
- Contract “pending” vs integration unchecked: **drift** if one updates without the other (recommend single status sentence ownership).

### 5. Consistency & honesty

- No **validated** language where checklists are unchecked.
- README / SCENARIO / contract all agree on where the Iteration 3 checklist lives.

---

## Done when

- [ ] `REVIEW_ITERATION_03_BACKPRESSURE.md` exists with **Severity** (`must` / `should` / `nice`) per finding, **Owner** (doc vs test vs defer), and **Evidence** (file + excerpt or line-of-sight).
- [ ] Explicit **“No issues”** section if the reviewer finds nothing material (unlikely but valid).
- [ ] **Out of scope** list for findings that belong in Iteration 4+ (schema strictness, etc.).

---

## Rules

- Prefer **5–15** findings total; merge duplicates.
- Do **not** rewrite streaming code in this sub-plan; file **suggestions** only.
- If a finding requires live stack or browser action, label **Operator** (or **Tier C Playwright** if automatable); avoid vague **Human** unless no harness exists yet.
