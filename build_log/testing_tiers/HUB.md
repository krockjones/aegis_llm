# Testing tiers — hub (A / B / C) & multi-sub-agent orchestration

**Policy source:** [TESTING_NOTES.md](../TESTING_NOTES.md) (Streaming — real-resource E2E).  
**Iteration link:** [PLAN_ITERATION_03C_TESTS.md](../PLAN_ITERATION_03C_TESTS.md).

---

## Roles

| Role | Count | Responsibility |
|------|-------|----------------|
| **Tier lead** | 1 per tier (A, B, C) | Holds **full implementation context** for that tier: reads all tier docs + `TESTING_NOTES.md` + affected tests; **delegates** to workers by pointing them at `WORKER_*` files; **merges** results; rejects scope creep. |
| **Tier worker** | **N** per tier (default **N = 3**) | **Narrow** slice in `WORKER_TierX_Wn.md`; reports back to **only** their tier lead (via PR thread or parent prompt). |

Leads **do not** implement other tiers’ files unless coordinating a shared doc touch (prefer one lead PR for doc, or sequential merges).

---

## Incremental runs (default expectation)

**You do not need a “true fan-out” in one go.** Coordinators may:

- Run **one worker** (`WORKER_B2` only), merge, then another worker days later.  
- Run **one tier** (e.g. A), ship, then **B** when compose/live bandwidth exists.  
- Have the **tier lead** implement W1→W3 in **one** Task (simplest), **or** spawn separate Tasks per worker over time and merge as each lands.

**True fan-out** (N parallel worker Tasks) is an **optional** speed-up when file ownership is disjoint and merge risk is acceptable—not a requirement of this layout.

---

## Artifacts (default N = 3)

| Tier | Lead plan | Workers |
|------|-------------|---------|
| **A** | [LEAD_TIER_A.md](./LEAD_TIER_A.md) | [WORKER_A1](./WORKER_A1.md), [WORKER_A2](./WORKER_A2.md), [WORKER_A3](./WORKER_A3.md) |
| **B** | [LEAD_TIER_B.md](./LEAD_TIER_B.md) | [WORKER_B1](./WORKER_B1.md), [WORKER_B2](./WORKER_B2.md), [WORKER_B3](./WORKER_B3.md) |
| **C** | [LEAD_TIER_C.md](./LEAD_TIER_C.md) | [WORKER_C1](./WORKER_C1.md), [WORKER_C2](./WORKER_C2.md), [WORKER_C3](./WORKER_C3.md) |

**Tier C scaffold (Open WebUI browser E2E):** [`tests/e2e_open_webui/README.md`](../../tests/e2e_open_webui/README.md)

---

## Spawn order (recommended)

1. **Tier A lead** (+ workers A1→A3 or lead executes all W in sequence) — keeps default CI green.  
2. **Tier B lead** (+ workers) — opt-in live / compose; **after** A merges if B touches same files (usually not).  
3. **Tier C lead** — optional; often **docs/scaffolding only** until Playwright + Open WebUI are pinned.

**Scaling N:** copy `WORKER_TierX_W3.md` → `W4.md`, add a row to the lead’s worker index table, and brief the new scope.

---

## Cursor / Task usage (coordinator)

**Preferred (incremental):** one Task at a time—lead completes **W1**, you review and merge; later another Task for **W2**, etc. Same for tiers: **A** merged before starting **B** if that reduces stress.

1. **Single-lead pass:** *“You are **Tier A lead** … complete `WORKER_A1` only”* (then repeat for A2, A3 on later runs), **or** *“… complete every `WORKER_A*` in order”* when you want one batch.  
2. **Next tier** when ready: repeat for **B**, then **C**. Parallel A+B+C Tasks only if paths are disjoint and you want throughput.  
3. **Fan-out (optional):** N Tasks for N workers in parallel—only when worth the merge coordination; see **Incremental runs**.

This repo ships **plans** here; **execution** is coordinator-driven via Task prompts above.
