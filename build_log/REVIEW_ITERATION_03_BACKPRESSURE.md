# Backpressure review — Iteration 3 streaming work (03A–D)

**Review sub-plan:** [PLAN_ITERATION_03E_BACKPRESSURE_REVIEW.md](./PLAN_ITERATION_03E_BACKPRESSURE_REVIEW.md)  
**Scope:** DRY, KISS, integration-test gaps vs docs, reasonable edge cases, cross-doc consistency.  
**Date:** 2026-04-11

---

## Summary

Prior sub-plan outputs are **honest** (pending operator, no fake validation). Main risks are **doc duplication** (DRY), a **`base_url` foot-gun** in the SDK snippet (edge case), and **unchanged** automated coverage for real-client streaming (expected gap, should stay visible).

---

## Remediation pass (2026-04-11)

Follow-up sub-agents applied review items where safe without human operator runs:

| Finding | Action |
|---------|--------|
| **E1** | `INTEGRATION_OPEN_WEBUI.md` — note under §1 header: criteria mirror `PLAN_ITERATION_03.md` §1; plan canonical on drift. |
| **E2** | Functional checklist Step 5 → pointer to **Streaming verification (Iteration 3)**. |
| **E3** | *(Earlier)* SDK env comment: no `/v1` in `AEGISLLM_GUARD_BASE_URL`. |
| **E4** | `INTEGRATION_OPEN_WEBUI.md` — Connection settings intro: WebUI origin-only vs SDK `.../v1` explicit. |
| **E5** | `API_CONTRACT.md` — Operational verification shortened; temporal status **only** in integration doc. |
| **E6** | `API_CONTRACT.md` — Known limitations (streaming) merged to one bullet. |
| **E7** | `SCENARIO_COVERAGE.md` — Gaps table row for SSE beyond respx / stretch tests. |
| **E8** | No change (defer). |
| **E9** | Replaced ad-hoc grep with `tests/test_contract_streaming_sentinel.py` (default CI) + Tier C Playwright for UI/stream wire where implemented. |

**Policy update (post-review):** Iteration 3 **§4.4** now **allows Tier B** real-resource streaming E2E (see `TESTING_NOTES.md`, `PLAN_ITERATION_03.md` §4.4, `PLAN_ITERATION_03C_TESTS.md`). E7-style gaps are **actionable** under the new policy, not “manual only” by default.

---

## Findings

| ID | Severity | Area | Finding | Owner | Evidence |
|----|----------|------|---------|-------|----------|
| E1 | **should** | DRY | **§1 criteria** appear in `PLAN_ITERATION_03.md` §1 and again in `INTEGRATION_OPEN_WEBUI.md`. Acceptable for sub-agent self-containment; **risk** is they drift if one table edits without the other. Mitigation: one-line pointer in integration doc (“canonical definition: parent plan §1”) or freeze wording and only edit in one place. | Doc | `PLAN_ITERATION_03.md` §1; `INTEGRATION_OPEN_WEBUI.md` § “Normative criteria” |
| E2 | **nice** | DRY | **Functional checklist** Step 5 (“Chat (stream)”) overlaps **Streaming verification** depth. Consider one cross-link from Step 5 to the Iteration 3 section to avoid two places defining “good stream” behavior. | Doc | `INTEGRATION_OPEN_WEBUI.md` L17–26 vs L28+ |
| E3 | **should** *(mitigated)* | KISS / edge | SDK example builds `base_url = f"{base}/v1"` — double `/v1` if env already includes `/v1`. **Mitigation:** comment added in `INTEGRATION_OPEN_WEBUI.md` next to the snippet (2026-04-11). | Doc | `INTEGRATION_OPEN_WEBUI.md` (SDK `base_url` block) |
| E4 | **nice** | Consistency | Connection settings say many UIs append `/v1` automatically; SDK block **always** appends `/v1`. Good but worth a single sentence that **SDK path differs from some UIs** to reduce confusion. | Doc | L13–14 vs L94–96 |
| E5 | **should** | Contract vs integration | **Operational verification** in `API_CONTRACT.md` paraphrases integration **Status**. If integration status text changes, contract can lie. **Mitigation:** contract bullet ends with “see integration doc status line” (already partially there)—consider stripping dynamic claims from contract and only pointing to integration for **temporal** state. | Doc | `API_CONTRACT.md` L107–109 |
| E6 | **nice** | KISS | **Known limitations (streaming)** second bullet partly repeats first. Could merge into one bullet (client variance + checklist pending). | Doc | `API_CONTRACT.md` L111–114 |
| E7 | **should** | Integration tests | Automated tests still **mock** Ollama NDJSON; no ASGI-level stream consumer test, no **auth + stream** test, no **mid-stream disconnect** test. Aligns with parent **§4.4 backlog**—not a defect of 03C, but a **visible hole** for reviewers. Optional follow-up: one opt-in live test marker in `SCENARIO_COVERAGE` Gaps table. | Test / doc | `test_chat.py` stream test; `SCENARIO_COVERAGE.md` Gaps |
| E8 | **nice** | Edge (code) | Streaming branch does not set `X-AegisLLM-Backend` (contract already notes asymmetry). UIs rarely care; no change required unless a client surfaced a bug. | Defer | `API_CONTRACT.md` ~L51–52 |
| E9 | **must** | Honesty | ✓ No false “validated” claims; checklists unchecked; contract says **pending**. **Keep** this invariant on any future edit (`tests/test_contract_streaming_sentinel.py` + Tier C stream tests). | CI / Tier C | `API_CONTRACT.md` L109; `tests/test_contract_streaming_sentinel.py` |

---

## No issues (material)

- **03C** no-op with existing stream tests passing is consistent with **§4.4** (no fabricated gaps).
- **README** single-line pointer is appropriately minimal.

---

## Out of scope (Iteration 4+ or separate work)

- Pydantic `extra="forbid"` on stream request bodies.
- Full SSE client matrix, proxy buffering, HTTP/2 edge cases.
- Mid-stream client cancel tests unless a real incident (**§4.4 backlog**).

---

## Suggested next actions (coordinator)

1. **Operator / CI:** Run integration §1 checklists and Tier C Playwright (`open_webui_e2e`) where applicable; then have **03B**-style pass update contract **Operational verification** with real §1.1 triplets (remove “pending” phrasing where appropriate).  
2. **Doc (quick):** Apply **E3** one-line guard on `AEGISLLM_GUARD_BASE_URL`.  
3. **Optional:** **E2** cross-link from functional Step 5 → Streaming verification.
