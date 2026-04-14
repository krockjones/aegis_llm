# Plan: Iteration 3 — Streaming as a product surface

**Parent:** [ITERATIONS.md](./ITERATIONS.md) · **Iteration 3**  
**Goal:** **Stream robustness** with **honest** contract language—**observed** behavior under a **capped** client set, “validated with X” only per **§1**, plus **known limitations**—without rewriting the streaming stack on speculation.

**Wording note:** “Product surface” means integrators can **predict** Guard’s stream behavior (SSE framing, error termination, chunk shapes) for the **documented** verification context—not a universal guarantee across all OpenAI-shaped clients.

**Explicit non-goal:** This iteration does **not** produce a **universal SSE / OpenAI streaming compatibility matrix** (browsers, proxies, every SDK, every UI). Scope stays: **Open WebUI** + **one official SDK** (or documented deferral of the SDK leg).

---

## 0. Cleanest pass (summary)

**Document roles (single pass each):** **§1** / **§1.2** = normative meaning of *validated* and who counts as a client. **§4** = what to put in each artifact (integration doc, contract, README pointer, tests, scenario map). **§5** = ordered steps only. **§6** = sign-off—must not restate §1 or §4 in new words.

**Outcomes this iteration ships:** integration write-up (streaming) · `API_CONTRACT.md` streaming subsection updated · `SCENARIO_COVERAGE.md` row touched if tests change · optional README one-liner. **Tests:** per **§4.4** — **default** mocked upstream (CI); **allowed and encouraged** where valuable: **E2E / integration tests with real resources** (compose, opt-in env, scripted stream clients) per [TESTING_NOTES.md](./TESTING_NOTES.md). **Code:** no `openai.py` / `ollama.py` stream-path refactors unless a run **forces** a fix.

### Sub-plans (sub-agents)

Assign **one sub-agent per file**; each file is self-contained with objective, tasks, and done-when. **Recommended order:** 03A → (03B and 03D in parallel) → 03C last or no-op → **03E** when you want a consolidation / risk pass before sign-off.

| ID | File | Agent focus | Depends on | Primary output |
|----|------|-------------|------------|------------------|
| **03A** | [PLAN_ITERATION_03A_INTEGRATION.md](./PLAN_ITERATION_03A_INTEGRATION.md) | Manual streaming verification + integration doc | — | `docs/INTEGRATION_OPEN_WEBUI.md` (or sibling) with §1 checklists + §1.1 |
| **03B** | [PLAN_ITERATION_03B_CONTRACT.md](./PLAN_ITERATION_03B_CONTRACT.md) | `API_CONTRACT.md` streaming validation / limitations | 03A | Contract subsection aligned with observed passes |
| **03C** | [PLAN_ITERATION_03C_TESTS.md](./PLAN_ITERATION_03C_TESTS.md) | Tier A mocked + **Tier B** real-resource streaming E2E (opt-in) | 03A notes (optional); `TESTING_NOTES.md` | Tests + skip/docs **or** explicit Tier B deferral |
| **03D** | [PLAN_ITERATION_03D_SCENARIO_README.md](./PLAN_ITERATION_03D_SCENARIO_README.md) | `SCENARIO_COVERAGE.md` + README pointer | 03A; 03C if tests changed | Updated scenario row; optional README line |
| **03E** | [PLAN_ITERATION_03E_BACKPRESSURE_REVIEW.md](./PLAN_ITERATION_03E_BACKPRESSURE_REVIEW.md) | **Read-only** review: DRY, KISS, integration holes, edge cases, honesty | 03A–D merged | [`REVIEW_ITERATION_03_BACKPRESSURE.md`](./REVIEW_ITERATION_03_BACKPRESSURE.md) |

**Coordinator note:** Sub-agents must **not** restate the full parent plan—each sub-plan inlines only what that agent needs. Escalate stream **code** changes to the parent plan owner (out of scope unless a manual pass **forces** a fix). **03E** does not ship product code unless findings are promoted to a separate task.

---

## 1. Definition: “validated” (operational)

A manual streaming pass counts as **validated** for a given client only if **all** of the following were **observed** and **recorded** (checkboxes in the integration doc are enough):

| Criterion | Meaning |
|-----------|---------|
| **Start** | Stream **begins** successfully (`200`, `text/event-stream`, first `data:` line(s) appear as expected). |
| **Incrementality** | **Chunks** arrive incrementally (not a single blob at the very end only)—at least two content-bearing chunks or equivalent client-visible token steps. |
| **Termination** | Stream **ends cleanly**: normal path reaches **`[DONE]`** (or client library reports completion without hang). |
| **Failure** | At least one **failure path** was exercised where feasible (e.g. upstream error or upstream stopped): **what the client showed** and **what appeared on the wire** (e.g. error `data:` + `[DONE]`) are **summarized** in the doc. |

Anything outside what was actually run is **not** “validated”—it belongs under **Known limitations** or stays unmentioned.

### 1.1 Provenance for contract claims

Whenever `docs/API_CONTRACT.md` (or the integration doc) says streaming was **validated**, the text must include **at minimum**:

- **Client name** (e.g. Open WebUI, OpenAI Python SDK).  
- **Rough version context** (e.g. Open WebUI image tag or app version; `openai` package version from `pip show`).  
- **Date** (or Guard / repo release identifier) so future readers can spot **drift**.

Claims must reflect **observed truth** only; if something was not tested, do not imply it.

---

### 1.2 Success boundary (iteration complete)

Iteration 3 is **done** when **all** of the following hold:

1. **Open WebUI** — manual streaming verification completed and written up per **§1** (*Definition: “validated”*).  
2. **Second client** — **either** manual streaming verification with **one official SDK** (default: **OpenAI Python SDK**, `stream=True`) **or** a short **explicit deferral** in the integration doc (reason + what would unblock it). No third or fourth client in scope unless the roadmap is rescoped.

Additional UIs or SDKs are **out of scope** for this iteration; note them as future work if discovered, do not chase them here.

---

## 2. Objective

An integrator or reviewer can answer:

| Question | Answer source |
|----------|----------------|
| Which setups were exercised for **streaming**, under what versions? | Integration doc (Open WebUI + **one** official SDK **or** explicit SDK deferral), each with §1.1 provenance |
| What **SSE** shape and **termination** does the code implement? | `docs/API_CONTRACT.md` + `errors.py` / `openai.py` |
| What is **not** guaranteed? | **Known limitations** (contract and/or integration doc) |
| What do **automated** tests cover vs **manual**? | `SCENARIO_COVERAGE.md` + test docstrings |

**Non-goals:** Full OpenAI stream parity; load testing; WebSocket; changing upstream Ollama NDJSON contract; **universal** SSE client matrix.

**Non-goals (tests):** Duplicating every `respx` mock scenario “just because”; deep dives (e.g. mid-stream cancel) **unless** a capped-client run proves a **real** problem (see §4.4 *Backlog*).

---

## 3. Code truth baseline (audit before implementing)

Paths are **relative to the monorepo root** (`aegis_learning_intelligence/`).

| Area | Location |
|------|----------|
| Stream route + exception → SSE | `zed_toolkit/services/aegis_llm/aegis_llm/routes/openai.py` — `chat_completions` → `StreamingResponse`, `gen()` |
| NDJSON → OpenAI chunks + `[DONE]` | `zed_toolkit/services/aegis_llm/aegis_llm/backends/ollama.py` — `chat_completion_stream` |
| SSE error + `[DONE]` | `zed_toolkit/services/aegis_llm/aegis_llm/errors.py` — `sse_error_termination` |
| Backend protocol | `zed_toolkit/services/aegis_llm/aegis_llm/backends/base.py` |
| Contract (streaming) | `zed_toolkit/services/aegis_llm/docs/API_CONTRACT.md` — *Streaming (SSE)* |
| Open WebUI manual pass | `zed_toolkit/services/aegis_llm/docs/INTEGRATION_OPEN_WEBUI.md` |
| Scenario map | `zed_toolkit/services/aegis_llm/build_log/SCENARIO_COVERAGE.md` |

**Tests today (streaming-related):**

| Test | What it proves |
|------|----------------|
| `tests/test_chat.py::test_chat_completions_stream` | Happy path: NDJSON upstream → SSE chunks + `[DONE]` (`scenario: chat-stream-sse`) |
| `tests/test_hardening.py::test_chat_stream_upstream_http_error` | Upstream HTTP error → SSE error payload + `[DONE]` in body |

**Gaps called out in SCENARIO_COVERAGE (stretch / backlog):** real NDJSON chunk boundaries vs respx; live stream against Ollama. Treat as **backlog** unless a **capped-client** manual run (**§1.2**) proves otherwise—do not pull into this iteration preemptively.

---

## 4. Deliverables

### 4.1 Integration checklist (capped clients)

**Client cap:** **§1.2** only (no third client in this iteration).

**Open WebUI** — extend `INTEGRATION_OPEN_WEBUI.md` (or sibling doc). Rows must be checkable against the §1 table (**Start** … **Failure**), not free-form narrative.

**Minimum scenarios:**

- **Stream on / stream off** — UI clears spinner / completes; no obvious truncated final token.  
- **Failure during stream** — upstream error or upstream stopped; record UI vs wire (error `data:` + `[DONE]` per `sse_error_termination` where applicable).  
- **Quirks** — Open WebUI–specific (base URL, `/v1`, model refresh) that affect streaming.

**Official SDK (default: OpenAI Python):** `base_url` = Guard origin; `api_key` aligned with Guard config; `stream=True`; record §1.1 provenance (package version, Python version, date) and observations against §1 table.

**Explicit deferral:** If the SDK leg is not run, the integration doc must state **deferred**, **why**, and **what would unblock** (concrete). Per **§1.2**, deferral is acceptable; vague omission is not.

### 4.2 Contract doc updates (`docs/API_CONTRACT.md`)

After integration checklists land: **Validation** bullets = §1.1 fields each; **Known limitations** = honest gaps only (see top-of-doc non-goal: no universal matrix, no “all clients”).

### 4.3 README

- At most **one** pointer line (e.g. “Streaming integration checks: see `docs/INTEGRATION_OPEN_WEBUI.md`”) if not already obvious; avoid duplicating the full checklist in README.

### 4.4 Tests (evidence-driven + real-resource E2E)

**Policy (inflection):** We **do** add **integration / E2E tests against real resources** when they are bounded, skippable, and documented (env flags, compose pins, `TESTING_NOTES.md`). They **complement** manual §1 checklists: automation proves **wire / Guard / real Ollama** behavior. **Open WebUI UI + streaming POST** should be covered by **Tier C Playwright** (`tests/e2e_open_webui/`) where feasible; reserve **manual** rows only for behaviors not yet automated (e.g. mid-stream failure UX, buffering quirks).

**Tier A — default CI (unchanged):** `respx` / mocked Ollama ASGI tests; fast, every PR.

**Tier B — in scope for new work:** Real Guard + real Ollama streaming (e.g. opt-in pytest module, compose smoke extension, `httpx`/`curl` stream consumer asserting `text/event-stream`, multiple `data:` chunks, `[DONE]`, optional error path). Must **skip** cleanly when resources absent; document env vars and image pins.

**Tier C — still gated:** Full Open WebUI browser automation (Playwright, etc.) — allowed as a **follow-on** if pinned; not required to close Iteration 3 if Tier B + manual Open WebUI §1 are satisfied.

**Also in scope:** bug or ambiguity from **manual or Tier B** runs; cheap lock-ins on ordering (error SSE before `[DONE]`).

**Backlog (heavy / incident-driven):** Prefer issues until a defect appears:

- **Mid-stream client cancel** — document + test when reproduction exists.  
- **Exotic chunk / role ordering** — only if a client misbehaves.  
- **Extra stream exception mirrors** — only if a gap is proven.

**Explicit non-goals:** unbounded SSE fuzzing; CI that only asserts “a stream test file exists”; running Tier B on every PR **without** skips/pins.

### 4.5 `SCENARIO_COVERAGE.md`

- Update the **SSE / NDJSON** row with any new test names and optional **live** column notes.  
- Refresh **Gaps** table if a backlog item is closed or a new one is discovered.

---

## 5. Execution order

Narrow run: **§1.2** client cap; paste §1 table before UI/SDK work (step 2); contract claims only **§1.1**; stream code unchanged unless a manual pass **forces** a fix.

| Step | Task | Output |
|------|------|--------|
| 1 | Re-read `openai.py`, `ollama.py`, `errors.py`, streaming section of `API_CONTRACT.md` | Short notes on actual guarantees |
| 2 | Copy §1 criteria into integration doc template (before any UI/SDK runs) | Checklist skeleton |
| 3 | Run Open WebUI manual pass against §1; record §1.1 provenance + quirks | Notes for doc |
| 4 | Run official SDK pass **or** write **Explicit deferral** (why + unblock criteria) | Doc update |
| 5 | Update `INTEGRATION_OPEN_WEBUI.md` (+ SDK subsection or sibling file if cleaner) | Docs |
| 6 | Patch `API_CONTRACT.md` — Validation (§1.1) + Known limitations | Docs |
| 7 | Add or extend tests per **§4.4** (mocked gaps **and/or** opt-in real-resource streaming E2E); document env/compose in `TESTING_NOTES.md` | Code |
| 8 | Update `SCENARIO_COVERAGE.md`; README pointer if needed | Docs |
| 9 | Commit in logical chunks (docs vs tests) | Git |

---

## 6. Acceptance checklist (Iteration 3 done when)

Sign-off only—detail lives in **§1**, **§1.2**, **§4**.

- [ ] **§1.2** satisfied (WebUI + SDK per §1 **or** explicit deferral).  
- [ ] **§4.1** integration doc complete (checkable vs §1; quirks noted).  
- [ ] **§4.2** `API_CONTRACT.md` updated; no matrix / “all clients” implication.  
- [ ] **§4.4** respected for new tests; existing stream tests still pass.  
- [ ] **§4.5** / **§4.3** as applicable (`SCENARIO_COVERAGE`, README pointer).

---

## 7. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Scope creep (rewrite streams) | §5 preamble + §0 outcomes; refactors only if integration forces |
| Client sprawl | **§1.2** |
| Integration drift / time sinks | §4.4 **Backlog** default |
| Overclaiming compatibility | §1.1 per validation bullet |
| Flaky live tests | Tier B: **skip** if Guard/Ollama missing; **pin** images; optional nightly job—not silent failures on every PR |
| Process overhead / doc bloat | **§0** roles: do not duplicate §1/§4 in acceptance or elsewhere |

---

## 8. Handoff to Iteration 4

**Iteration 4** (schema / `extra="forbid"`, stricter validation) can assume streaming **behavior and docs** match **documented** §1 passes (Open WebUI + SDK or deferral). Re-run a **short** stream smoke after Pydantic tightening before release.

---

## 9. Review notes (incorporated)

- Parent: `ITERATIONS.md` §Iteration 3; aligned with `PLAN_ITERATION_01` / `PLAN_ITERATION_02`.  
- Code baseline: §3.  
- Revision: **§0** document roles + trimmed overlap; removed standalone execution-guidance section (discipline folded into **§5** preamble); **§6** acceptance by reference only. **§4.4** expanded: **real-resource E2E / integration streaming tests** allowed alongside manual §1 (see `TESTING_NOTES.md`).
