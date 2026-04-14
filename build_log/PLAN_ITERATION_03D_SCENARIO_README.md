# Sub-plan 03D — Scenario map & README pointer

**Parent:** [PLAN_ITERATION_03.md](./PLAN_ITERATION_03.md) · **Agent role:** light docs / discoverability  
**Primary artifacts:** [`build_log/SCENARIO_COVERAGE.md`](./SCENARIO_COVERAGE.md) · [`README.md`](../README.md)

**Depends on:** [03A](./PLAN_ITERATION_03A_INTEGRATION.md); if [03C](./PLAN_ITERATION_03C_TESTS.md) adds tests, include those names here.  
**Blocks:** nothing.

---

## Objective

Keep the **scenario → test** map honest after Iteration 3 doc/test work, and ensure operators can find streaming checks without duplicating the full checklist in README (parent **§4.3**, **§4.5**).

---

## Tasks

1. **`SCENARIO_COVERAGE.md`** — Update the **SSE / NDJSON streaming** row: integration/live column notes if 03A changed recommended manual steps; add test names if 03C added tests. Refresh **Gaps** table only if something closed/opened.  
2. **`README.md`** — At most **one** pointer to streaming integration doc if not already obvious (parent **§4.3**). Skip if README already links adequately.

---

## Done when

- [ ] SSE/streaming row matches repo reality.  
- [ ] README not bloated; pointer added only if needed.
