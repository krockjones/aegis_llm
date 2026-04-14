# Tier C lead — Open WebUI / browser E2E (optional)

**You are the Tier C lead sub-agent.** Own Tier C context: Playwright smoke, compose profile, and optional expansion (chat flows, RAG).

## Context bundle

- [INTEGRATION_OPEN_WEBUI.md](../../docs/INTEGRATION_OPEN_WEBUI.md)  
- [HUB.md](./HUB.md), [TESTING_NOTES.md](../TESTING_NOTES.md) Tier C row  
- [`docker-compose.yml`](../../docker-compose.yml) — service **`open-webui`** (`--profile tier-c`)  
- [`tests/e2e_open_webui/`](../../tests/e2e_open_webui/) — `conftest.py`, `test_open_webui_reachable.py`, `README.md`  
- [`pyproject.toml`](../../pyproject.toml) optional extra **`e2e`**, marker **`open_webui_e2e`**

## Team (N = 3)

| Worker | File | Focus |
|--------|------|--------|
| C1 | [WORKER_C1.md](./WORKER_C1.md) | Directory + README for future Playwright tree |
| C2 | [WORKER_C2.md](./WORKER_C2.md) | Pinning policy (Open WebUI image digest placeholder) |
| C3 | [WORKER_C3.md](./WORKER_C3.md) | CI matrix note (optional nightly job doc only) |

## Lead duties

1. **Shipped baseline:** C1–C3 are satisfied (README, pinning section, nightly outline) **plus** minimal Playwright test and compose `tier-c` profile.  
2. **Extensions:** add workers (C4+) for chat streaming in UI, RAG, auth—each with its own `WORKER_` spec.  
3. **Do not** block Tier A/B merges.

## Out of scope (until funded)

Long multi-step UI suites without pinned Open WebUI digests in CI.
