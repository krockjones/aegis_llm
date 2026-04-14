# Sub-plan 03C — Streaming tests (mocked + real-resource E2E)

**Parent:** [PLAN_ITERATION_03.md](./PLAN_ITERATION_03.md) · **Agent role:** tests only  
**Orchestration:** [testing_tiers/HUB.md](./testing_tiers/HUB.md) — **Tier leads** (A/B/C) each own **N=3 workers** under `testing_tiers/`.  
**Primary locations:** `zed_toolkit/services/aegis_llm/tests/`, compose / scripts if extending smoke

**Depends on:** [03A](./PLAN_ITERATION_03A_INTEGRATION.md) optional for repro cases; [TESTING_NOTES.md](./TESTING_NOTES.md) for tiering policy.  
**Blocks:** [03D](./PLAN_ITERATION_03D_SCENARIO_README.md) if you add or rename tests (scenario row).

---

## Objective

Maintain **Tier A** (mocked) coverage and **add Tier B** where useful: **integration / E2E streaming against real Guard + real Ollama**, skippable and documented—per parent **§4.4** and **TESTING_NOTES.md** (*Streaming — real-resource E2E*). **Tier C** (browser Open WebUI) remains optional.

---

## Tiers (short)

| Tier | Role |
|------|------|
| **A** | `respx` NDJSON → SSE; every PR (`test_chat_completions_stream`, `test_chat_stream_upstream_http_error`). |
| **B** | Real `POST /v1/chat/completions` `stream: true`; assert stream shape (`text/event-stream`, multiple chunks, `[DONE]`); optional failure path. Env/compose gated; **skip** if not up. |
| **C** | Playwright (or similar) against Open WebUI — only if explicitly scoped. |

---

## Tasks

1. Keep Tier A green; extend only if a gap appears.  
2. **Tier B (new work):** Add or extend opt-in test(s) or compose smoke (e.g. `curl -N` / httpx) documented in `TESTING_NOTES.md` and `SCENARIO_COVERAGE.md`. Use same URL env conventions as existing live tests where possible.  
3. If Tier B is not implemented in this pass, document **why** (time vs priority) in PR or a one-line note in `TESTING_NOTES.md`—**no-op on Tier B alone** is acceptable if Tier A holds and manual §1 proceeds.

---

## Done when

- [ ] Tier A stream tests still pass.  
- [ ] Either Tier B increment landed (with skip + doc) **or** explicit deferral of Tier B for this PR with reason.  
- [ ] **§4.4 backlog** items (mid-stream cancel, etc.) still incident-driven unless promoted.
