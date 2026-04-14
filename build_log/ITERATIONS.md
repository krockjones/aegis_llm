# Wedge iterations — action roadmap

Derived from a blunt product/engineering review of the current alpha. Each iteration has **one core focus**. Order matters: contract and posture before deeper protocol work.

## Cross-cutting rules (every iteration)

- **Narrow positioning:** Ollama-first; a single production-grade backend until a second is fully justified and shippable.
- **No story inflation:** README, product spec rows, and public copy stay aligned with what is implemented **today**.

---

## Iteration 1 — Declared API contract (boundaries, not features)

**Core focus:** Move from “OpenAI-compatible” to **compatibility with explicit, reviewable boundaries** (integrators and reviewers can verify claims against this doc and the cited code—not machine-certified unless we add contract tests later).

**Deliverables**

- One **supported subset** document (README section and/or `docs/API_CONTRACT.md`): endpoints, methods, important request fields, streaming vs non-stream, embeddings limits (`encoding_format`, etc.), intentionally unsupported areas (tools, images, audio, batch, …).
- **Backends today:** state clearly that only **Ollama** is supported in production; factory/abstraction is internal, not a multi-backend product promise.

**Done when**

- A new integrator can read once and know what works, what does not, and what is approximate.

**Avoid**

- New endpoints added only to “look more OpenAI.” This iteration is documentation plus, at most, small clarifying error messages.

---

## Iteration 2 — Deployment posture (warnings, not nanny defaults)

**Core focus:** **Declared product stance** at runtime: surface risky setups without ruining localhost developer experience.

**Deliverables**

- Startup **warnings** (stderr / diagnostics), e.g. listening on all interfaces with **no API keys**, with a short reason and pointer to docs.
- README **defaults matrix:** localhost vs LAN vs exposed host—assumptions and recommendations.

**Done when**

- Risky combinations are **visible at boot**; typical local dev stays quiet (or a single INFO, not alarm spam).

**Avoid**

- Changing defaults to stricter behavior without an explicit version/changelog note. This pass is **visibility**, not a breaking security overhaul.

---

## Iteration 3 — Streaming as a product surface

**Core focus:** **Stream robustness** under real clients **and** reproducible automation: **manual checklists** (Open WebUI + one SDK) **plus** **E2E / integration tests with real resources** where they add signal (compose, opt-in live, scripted stream consumers)—not mocked-upstream alone.

**Deliverables**

- Short **integration checklist** (e.g. Open WebUI + one SDK): scenarios exercised, quirks noted.
- **Tests:** default CI stays fast (respx / mocked Ollama); **add** opt-in or compose-backed tests that hit **real** Guard→Ollama streaming (SSE, `[DONE]`, error paths) per [TESTING_NOTES.md](./TESTING_NOTES.md) streaming policy. Manual runs and automation **both** feed §1.1-style provenance where applicable.

**Done when**

- The contract doc can honestly say “validated with X” (**Tier C Playwright**, Tier B live tests, **and/or** other pinned automated runs) or list **known** stream limitations.

**Avoid**

- Rewriting the streaming stack preemptively; letting **only** flaky unbounded UI tests drive CI—prefer skips, pins, and opt-in markers for real-resource runs.

---

## Iteration 4 — Schema and validation discipline

**Core focus:** Public contract feels **intentional**, slightly less permissive by accident.

**Deliverables**

- Tighten Pydantic models where safe: e.g. `extra="forbid"` on selected bodies (if compatible with target clients), stricter types on hot fields, stable 400 messages.
- Update the Iteration 1 contract doc to match.

**Done when**

- Unexpected or future-only OpenAI fields fail **predictably** with stable error shapes.

**Avoid**

- Breaking common clients; validate against the Iteration 3 checklist before tightening.

---

## Iteration 5 — Abstraction hygiene (internal only)

**Core focus:** Keep the **backend boundary** useful **without** selling a multi-backend product.

**Execution detail:** [PLAN_ITERATION_05.md](./PLAN_ITERATION_05.md).

**Deliverables**

- Brief architecture note (code comment or doc): protocol exists for tests and future backends; **no second backend** in this iteration without a concrete wedge customer.
- Optional: complete the `Backend` protocol typing (e.g. `health_probe`) to reduce confusion.

**Done when**

- Repo and docs do not imply “pick your backend” for production beyond Ollama.

**Avoid**

- Adding vLLM, LM Studio, etc. solely to justify the factory—explicit anti-goal per review.

---

## Optional (non-blocking)

- **Founder-style wedge memo:** ICP, why this layer vs raw Ollama, distribution—strategy artifact only; does not block Iterations 1–5. **Draft (repo root):** [`docs/product/AEGISLLM_GUARD_WEDGE_ONE_PAGER.md`](../../../../docs/product/AEGISLLM_GUARD_WEDGE_ONE_PAGER.md).

---

## Summary

| Iteration | Core focus | Primary output |
|-----------|------------|----------------|
| 1 | Contract story | Bounded API documentation |
| 2 | Deployment posture | Startup warnings + defaults matrix |
| 3 | Stream robustness | Manual §1 + real-resource streaming E2E (opt-in) + contract |
| 4 | Schema strictness | Tighter validation + doc sync |
| 5 | Abstraction hygiene | Honest Ollama-only positioning |

---

## Review context (why this order)

The codebase reads as a **credible alpha**: scope discipline, honest positioning, clear structure, real failure paths, incremental hardening. Remaining risks cluster around **protocol edge behavior** (especially streams), **deployment clarity**, and **product drift** (broadening the story before the wedge is earned). This roadmap keeps engineering narrow, trustworthy, and unsurprising in front of local backends.
