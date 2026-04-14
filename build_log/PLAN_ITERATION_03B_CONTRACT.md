# Sub-plan 03B — API contract streaming section

**Parent:** [PLAN_ITERATION_03.md](./PLAN_ITERATION_03.md) · **Agent role:** contract / technical accuracy  
**Primary artifact:** [`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md) — *Streaming (SSE)* and related bullets only (touch other sections only if a streaming claim forces consistency)

**Depends on:** [03A](./PLAN_ITERATION_03A_INTEGRATION.md) complete enough to supply **§1.1** facts (client, version, date per validated surface).  
**Blocks:** none (can parallel with [03D](./PLAN_ITERATION_03D_SCENARIO_README.md) after 03A).

---

## Objective

Update the canonical contract so streaming **Validation** reflects **observed** manual passes only, with **Known limitations** honest and **no** universal compatibility matrix (parent explicit non-goal).

---

## Rules

- Each **Validation** bullet = one observed surface and must include **client name**, **rough version**, **date** (same bar as parent **§1.1**). **Tier B** automated runs count if provenance includes job/compose id and image pins (see `build_log/TESTING_NOTES.md`).  
- Do **not** claim “all OpenAI clients” or imply full SSE matrix coverage.  
- **Known limitations:** only gaps you verified or can state as unknown—no filler.

---

## Tasks

1. Re-read `docs/API_CONTRACT.md` *Streaming (SSE)* + `aegis_llm/errors.py` (`sse_error_termination`), `routes/openai.py` stream branch—ensure contract text still matches code.  
2. Add **Validation** (or **Operational verification**) under streaming, sourced from 03A integration doc.  
3. Tighten **Known limitations** if 03A exposed real gaps; otherwise minimal/no change.

---

## Done when

- [ ] Streaming subsection reflects 03A outcomes; every “validated” claim has §1.1 triplet.  
- [ ] No matrix / “all clients” wording.  
- [ ] Code-doc mismatch fixed **in the doc** unless a code bug was found—in the latter case, note for parent (code change is out of scope for 03B unless explicitly escalated).
