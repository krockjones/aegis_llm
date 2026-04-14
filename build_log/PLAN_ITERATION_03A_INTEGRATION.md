# Sub-plan 03A — Integration doc & manual streaming verification

**Parent:** [PLAN_ITERATION_03.md](./PLAN_ITERATION_03.md) · **Agent role:** integration / operator-facing docs (manual passes + structured write-up)  
**Primary artifact:** [`docs/INTEGRATION_OPEN_WEBUI.md`](../docs/INTEGRATION_OPEN_WEBUI.md) (or a sibling under `docs/` if you split SDK content—stay linked from README if so)

**Depends on:** nothing (run first among 03-subplans).  
**Blocks:** [03B](./PLAN_ITERATION_03B_CONTRACT.md) (contract validation bullets should cite what 03A recorded).

---

## Objective

Produce a **checkable** streaming integration write-up for the **§1.2 client cap**: **Open WebUI** + **either** official **OpenAI Python SDK** (`stream=True`) **or** an **explicit deferral** (why + concrete unblock). No third client.

**Automation:** **Tier B** real-resource streaming tests (see [TESTING_NOTES.md](./TESTING_NOTES.md)) can support wire-level §1 rows **for scripted clients**. **Tier C Playwright** (`tests/e2e_open_webui/`) covers Open WebUI **browser + Network** streaming where implemented; keep **manual** checklist rows only for gaps (failure UX, quirks) not yet expressed as tests.

---

## Normative criteria (copy into the integration doc as the checklist header *before* running UI/SDK)

A pass is **validated** for that client only if **all** rows were observed and recorded (checkboxes OK):

| Criterion | Meaning |
|-----------|---------|
| **Start** | `200`, `text/event-stream`, first `data:` as expected |
| **Incrementality** | ≥ two content-bearing chunks (or equivalent visible token steps) |
| **Termination** | Clean end; normal path includes **`[DONE]`** on wire or SDK completion without hang |
| **Failure** | At least one failure path where feasible; **UI vs wire** summarized |

**Provenance (§1.1)** — for every client row, record: **client name**, **rough version** (image tag / app version / `pip show openai`), **date** (or Guard release id).

---

## Tasks

1. **Skeleton** — Paste the table above into `INTEGRATION_OPEN_WEBUI.md` (new “Streaming verification” section or equivalent).  
2. **Open WebUI** — Run scenarios in parent **§4.1** minimum list (stream on/off, failure during stream, quirks). Fill the §1 rows + §1.1 for WebUI.  
3. **Second client** — Run OpenAI Python `stream=True` against Guard **or** add subsection **Explicit deferral** with why + unblock. Fill §1 + §1.1 for SDK, or document deferral only.  
4. **Out of scope** — If you discover another UI/SDK worth testing, **one line** future work only; do not expand this sub-plan.

---

## Done when

- [ ] Integration doc contains checkable §1 table(s) per client (or deferral block meeting **§1.2**).  
- [ ] §1.1 provenance present for every non-deferred client.  
- [ ] Quirks and failure-path wire notes captured where parent **§4.1** requires.

---

## Handoff to 03B

Leave the integration doc in a state where another agent can **copy validation bullets** into `API_CONTRACT.md` with matching client names + versions + dates.

## Remaining “Done when” — subagent split

Operator-only streaming evidence and provenance are split into **`PLAN_ITERATION_03A_SUBAGENT_BRIEFS.md`** (roles **03A-O1** through **03A-O4**) with copy-paste **Task** prompts and merge order. Paste targets are pre-provisioned in **`docs/INTEGRATION_OPEN_WEBUI.md`** (Wire notes / Quirks blocks).
