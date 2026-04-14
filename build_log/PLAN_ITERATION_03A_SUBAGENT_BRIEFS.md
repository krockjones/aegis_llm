# Subagent briefs — close remaining **03A “Done when”**

**Parent:** [PLAN_ITERATION_03A_INTEGRATION.md](./PLAN_ITERATION_03A_INTEGRATION.md)  
**Canonical paste target:** [`docs/INTEGRATION_OPEN_WEBUI.md`](../docs/INTEGRATION_OPEN_WEBUI.md) (sections **Wire notes** / **Quirks** / checklist + §1.1 tables)

These roles split work that **requires a live machine** (browser, Docker, Ollama). Prefer **Tier C Playwright** (`tests/e2e_open_webui/`) for repeatable UI + Network evidence; use subagents / operators for **provenance commands**, **paste formatting**, and **gaps not yet automated** (e.g. mid-stream failure UX). The **coordinator** merges PRs.

**Hard rule:** Do **not** tick normative checklist rows or write “validated” until evidence in this repo matches the criterion. Redact secrets and long tokens in wire pastes.

---

## Role **03A-O1** — Stream on / stream off (Open WebUI + wire)

**Goal:** Evidence for plan **section 1** rows **Start**, **Incrementality**, **Termination** (happy path) for **Open WebUI** only.

**Operator steps (browser session or Playwright trace review):**

1. Stack up: Guard + Ollama + Open WebUI; pick a model from Guard’s model list.
2. DevTools → **Network**; filter `chat/completions` or `completions` (your build’s path).
3. **Stream on:** send a short prompt; confirm UI shows incremental tokens; capture **one** streaming request: status, `Content-Type`, first `data:` line, two distinct content-bearing `data:` lines (or explain visible UI incrementality if wire is opaque), and final stream end (`[DONE]` on wire if present).
4. **Stream off:** repeat with streaming disabled (Chat Controls / UI toggle); capture status + body shape (single JSON vs SSE).

**Deliverable:** Paste into `docs/INTEGRATION_OPEN_WEBUI.md` → **Wire notes — stream on / stream off**. Then edit the **§1 checklist — Open WebUI** lines for Start / Incrementality / Termination: change `[ ]` → `[x]` **only** if every cited criterion is met; otherwise leave `[ ]` and add one sentence under the paste block explaining the gap.

**Subagent prompt (copy into Cursor Task / subagent):**

```text
Read zed_toolkit/services/aegis_llm/build_log/PLAN_ITERATION_03A_SUBAGENT_BRIEFS.md role 03A-O1.
Read zed_toolkit/services/aegis_llm/docs/INTEGRATION_OPEN_WEBUI.md (Streaming verification + Wire notes sections).
Do not claim validation without evidence. Output: (1) markdown text ready to paste into "Wire notes — stream on / stream off"; (2) exact edits for the three §1 checklist lines (checkbox + one-line evidence suffix) or explicit "leave unchecked because …". No fabricated timings or HTTP bodies.
```

---

## Role **03A-O2** — Failure during stream (UI vs wire)

**Goal:** Evidence for plan **section 1** row **Failure** (Open WebUI).

**Safety:** Prefer stopping **Ollama** mid-reply in a **dev** stack only; avoid data loss; restore `ollama serve` after.

**Operator steps:**

1. Start a **streaming** reply with Network open on the same request as O1.
2. Stop upstream (e.g. `ollama stop` / kill serve) **after** first chunks appear.
3. Record **UI** (spinner, error toast, partial text). Record **wire** (last `data:` lines, HTTP status if connection drops, presence/absence of error-shaped payloads; cite `aegis_llm/errors.py` `sse_error_termination` only if you observed matching behavior).

**Deliverable:** Paste into **Wire notes — failure during stream**; update **Failure** checklist line only if the scenario actually ran and evidence is pasted.

**Subagent prompt:**

```text
Read build_log/PLAN_ITERATION_03A_SUBAGENT_BRIEFS.md role 03A-O2 and docs/INTEGRATION_OPEN_WEBUI.md.
Produce: (1) paste-ready "UI vs wire" markdown for the failure scenario template; (2) recommended checkbox state for Failure + one-line justification. If operator has not run the scenario, output explicit "blocked: …" only—no tick.
```

---

## Role **03A-O3** — §1.1 provenance (versions + Guard context)

**Goal:** Fill **§1.1 provenance — Open WebUI** (and optionally SDK table) with **facts**, not UI ad banners.

**Commands (operator runs on host; subagent formats output):**

- Open WebUI image: from compose dir, e.g. `docker compose --profile tier-c images open-webui` and/or `docker inspect <container> --format '{{.Config.Image}}'` and digest if available.
- Guard: `git rev-parse HEAD` in `zed_toolkit/services/aegis_llm` (or release tag in use).
- SDK (if claiming SDK client): `pip show openai` + `python -V`.

**Deliverable:** Update the two **§1.1** tables in `INTEGRATION_OPEN_WEBUI.md` with non-placeholder **Version** and **Date / Guard context** cells.

**Subagent prompt:**

```text
Read PLAN_ITERATION_03A_SUBAGENT_BRIEFS.md role 03A-O3.
Operator will paste raw command outputs. Your job: turn them into clean table cell values for INTEGRATION_OPEN_WEBUI.md §1.1 (Open WebUI + optional SDK). Flag banner-vs-image mismatch. Do not tick §1 rows—provenance only.
```

---

## Role **03A-O4** — Second client (OpenAI Python SDK) or explicit deferral

**Goal:** Satisfy parent **PLAN_ITERATION_03.md** §1.2 second client: **either** run SDK `stream=True` and fill SDK §1 + §1.1 **or** add subsection **Explicit deferral — OpenAI Python SDK** with **why** + **what unblocks** (required if SDK leg is skipped).

**Subagent prompt:**

```text
Read PLAN_ITERATION_03.md §1.2 and docs/INTEGRATION_OPEN_WEBUI.md Second client section.
If coordinator chose deferral: write 3–6 sentence "Explicit deferral" subsection (why, unblock, target date optional) and ensure Open WebUI §1 can still be closed independently.
If coordinator chose run: produce a minimal runbook + paste templates for SDK wire notes (or cite Tier B pytest provenance per integration doc rules) and checklist line edits—no false ticks.
```

---

## Coordinator merge order

1. **03A-O3** (versions) — avoids editing checkboxes twice.  
2. **03A-O1** then **03A-O2** (evidence + checklist).  
3. **03A-O4** (SDK or deferral).  
4. Refresh **Status** paragraph in `INTEGRATION_OPEN_WEBUI.md` once checkboxes match reality.  
5. Optional **03B** pass on `docs/API_CONTRACT.md` if contract “pending” language must track new §1.1 triplets.

---

## Parallelization

- **03A-O1** and **03A-O3** can run in parallel (Playwright / `curl` wire vs `docker inspect` provenance).  
- **03A-O2** should run **after** a successful O1 stream-on path (shared Network practice).  
- **03A-O4** is independent once policy (run vs defer) is decided.
