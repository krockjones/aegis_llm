# Plan: Iteration 2 — Deployment posture (warnings, not nanny defaults)

**Parent:** [ITERATIONS.md](./ITERATIONS.md) · **Iteration 2**  
**Goal:** **Surface risky deployment posture at startup** (one high-signal warning where it matters), add a small **README defaults matrix**, and keep **localhost quiet**—without changing security defaults or behavior unless paired with an explicit version/changelog note.

**Wording note:** This iteration is **narrow visibility**, not a pseudo-security framework. One targeted boot warning + clearer docs beats many marginal messages.

---

## 0. Cleanest pass (summary)

- Add **one** startup **WARNING** for **wide bind + no API keys** (see §3.1).  
- Keep **localhost** quiet (no spam for normal dev).  
- Add a compact **defaults matrix** to README (local dev / LAN·container / exposed).  
- **Do not** change defaults (`listen_host`, CORS, auth semantics).  
- **Do not** add a second product around “deployment safety”—no extra warnings this iteration unless rescoped.

---

## 1. Objective

An operator can see **at boot** whether they hit the main accidental-exposure case, and can read **one matrix** for typical profiles:

| Question | Answer source |
|----------|----------------|
| Am I in the **wide bind + no keys** case? | stderr **WARNING** + existing diagnostics line |
| What should I use for **local vs LAN vs exposed**? | README **defaults matrix** |
| Where are CORS, public routes, and `/v1/*` auth documented? | README **Security / deployment** + [docs/API_CONTRACT.md](../docs/API_CONTRACT.md) |
| Did defaults change? | **No** in this iteration |

**Non-goals (behavior):** Stricter defaults, refuse-to-start, nanny enforcement.

**Non-goals (inference):** The app **does not** infer real-world exposure from the environment. No detection of Docker port publishing, cloud load balancers, reverse proxies, or OS firewall state. The warning is **only** from configured `listen_host` + presence of API keys—not “are we on the internet.” That keeps scope honest and avoids false confidence.

---

## 2. Code truth baseline (audit before implementing)

Paths are **relative to the monorepo root** (`aegis_learning_intelligence/`).

| Area | Location |
|------|----------|
| Startup (load settings → diagnostics → Uvicorn) | `zed_toolkit/services/aegis_llm/aegis_llm/main.py` |
| Structured diagnostics line | `zed_toolkit/services/aegis_llm/aegis_llm/diagnostics.py` — `print_startup_diagnostics` |
| `Settings`, `load_settings` (defaults, keys, timeouts) | `zed_toolkit/services/aegis_llm/aegis_llm/config.py` |
| CORS | `zed_toolkit/services/aegis_llm/aegis_llm/app.py` — `CORSMiddleware` |
| Auth, public paths | `zed_toolkit/services/aegis_llm/aegis_llm/middleware/auth.py` |
| Operator prose | `zed_toolkit/services/aegis_llm/README.md` |
| HTTP / auth boundaries | `zed_toolkit/services/aegis_llm/docs/API_CONTRACT.md` |

**Today:** one stderr diagnostics line; no deployment WARNING tier.

---

## 3. Deliverables

### 3.1 Startup warning (single primary rule)

Emit **one** **WARNING** when **all** of the following hold:

- `listen_host` is exactly **`0.0.0.0`** or **`::`** (string match after the same normalization `Settings` already uses—**no** extra variants in v1 of this check; expand only if production evidence demands it).
- `api_keys` is **empty** → Bearer is **not** required on **`/v1/*`**.

**Warning copy (requirements):**

- State clearly that the concern is **unauthenticated access to `/v1/*`** (not “the whole server is open” or “everything is authenticated”—the public-route story is nuanced: `/`, `/healthz`, `/readyz`, `/docs`, `/openapi.json`, `/redoc` stay public even with keys; say **only** what this warning is about).
- One line (or two short lines max): risk + pointer to README Security and/or `docs/API_CONTRACT.md`.

**Placement:** Run the check **after** successful `load_settings()` and **before** `uvicorn.run` (same neighborhood as `print_startup_diagnostics`) so it appears **before** Uvicorn dominates the console.

**Mechanism:** Implement however is simplest (extend `diagnostics.py` with a second stderr line, or a one-line logger WARNING). The plan does not prescribe Option A vs B—the outcome is what matters: **visible, once, at the right time.**

**Quiet localhost rule:** If `listen_host` is **not** `0.0.0.0` / `::`, **or** API keys are set, **no** deployment warning. Do not add secondary or INFO “helpful” lines in this iteration—that avoids scope creep.

**Explicit non-goals:**

- Do **not** change default `listen_host`, CORS, or API key behavior.  
- Do **not** fail fast on risky combos without a **separate** breaking-change release.  
- **No secondary warnings** in Iteration 2 (e.g. “you have keys but docs are public”)—README already covers that.

### 3.2 README defaults matrix

Add a compact table (under or beside **Security / deployment**). Rows: **Local dev**, **LAN / container**, **Exposed / production**. Columns (honest to **current** code):

- Typical `AEGISLLM_LISTEN_HOST`  
- API keys recommendation  
- CORS note (`allow_origins=["*"]` today—**not** env-tunable; restrict at proxy if needed)  
- Public routes pointer (link `docs/API_CONTRACT.md`)  
- Optional: link to Iteration 2 warning behavior (“wide bind + no keys → WARNING at startup”)

### 3.3 `docs/DEPLOYMENT.md`

**Default: do not add.** The matrix + existing Security section should be enough. Add a separate deploy doc **only** if README becomes overcrowded after the matrix lands.

### 3.4 Tests (lightweight)

- Unit-test the predicate: warn iff (`0.0.0.0` or `::`) ∧ empty keys; **no** warn for `127.0.0.1` + empty keys; **no** warn for `0.0.0.0` + keys set.  
- Prefer a small pure helper (e.g. `deployment_warn_wide_bind_no_auth(s: Settings) -> bool`) plus optional stderr capture.

### 3.5 Changelog / version

Docs + warning-only, no default change: brief release note is enough. Any future default tightening is **not** Iteration 2.

---

## 4. Execution order

| Step | Task | Output |
|------|------|--------|
| 1 | Re-read `config.py`, `diagnostics.py`, `main.py`, `auth.py` | Confirmed predicates |
| 2 | Implement single WARNING + tests | Code |
| 3 | README defaults matrix | Docs |
| 4 | Self-review: warning text names `/v1/*`, does not misstate public routes | Checklist |
| 5 | Commit in small chunks (e.g. warning+tests, then README) | Git |

---

## 5. Acceptance checklist (Iteration 2 done when)

- [ ] **`0.0.0.0` or `::`** and **empty** `api_keys` → **one** clear **WARNING** at startup, **before** Uvicorn’s usual flood.  
- [ ] Warning text explicitly references **unauthenticated `/v1/*`** and does **not** imply every route shares the same auth story.  
- [ ] **`127.0.0.1`** (typical dev) + empty keys → **no** new deployment warning.  
- [ ] **`0.0.0.0`** + non-empty keys → **no** deployment warning (this iteration’s single rule only).  
- [ ] Diagnostics line in `diagnostics.py` remains (may extend; do not remove without cause).  
- [ ] README **defaults matrix** present; CORS described as **fixed in code** unless env support is added.  
- [ ] **No** default behavior change without changelog.  
- [ ] Tests cover the predicate (and optional stderr).  
- [ ] **No** `docs/DEPLOYMENT.md` unless README truly needs relief.

---

## 6. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Annoying devs | Warn only **wide bind ∧ no keys**; one message |
| Odd `listen_host` spellings | v1: **only** `0.0.0.0` and `::`; extend later with evidence |
| Docs drift | Matrix + contract link; update when `auth.py` or CORS changes |
| Scope creep | No secondary warnings; no environment inference |

---

## 7. Handoff to Iteration 3

**Iteration 3** (streaming / real clients) can assume deployment posture is **documented** and **one** boot warning covers the main LAN exposure foot-gun; no need to duplicate in stream tests.

---

## 8. Review notes (incorporated)

- Relative **repo** paths in §2; plainer goal wording; **narrow** bind list; **trimmed** Option A/B to outcome-only; **explicit** non-goal on inferring Docker/LB/proxy/firewall; **warning copy** must name **`/v1/*`** and respect public-route nuance; **no** secondary warnings; **skip** `DEPLOYMENT.md` by default; **§0** clean summary.
