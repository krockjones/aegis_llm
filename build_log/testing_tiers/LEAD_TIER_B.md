# Tier B lead — real Guard + Ollama streaming (opt-in)

**You are the Tier B lead sub-agent.** Own **all** Tier B context and keep workers on track.

## Context bundle (read first)

- [TESTING_NOTES.md](../TESTING_NOTES.md) — *Streaming — real-resource E2E*  
- `tests/test_integration_live.py`, `pytest.ini` / `[tool.pytest.ini_options]` in `pyproject.toml`  
- `scripts/smoke_compose.sh`, `docker-compose.yml` (if present at service root)  
- [SCENARIO_COVERAGE.md](../SCENARIO_COVERAGE.md) — Gaps + SSE row  

## Team (N = 3)

| Worker | File | Focus |
|--------|------|--------|
| B1 | [WORKER_B1.md](./WORKER_B1.md) | Opt-in live pytest: `POST /v1/chat/completions` `stream: true` |
| B2 | [WORKER_B2.md](./WORKER_B2.md) | Model discovery from `GET /v1/models` + skip rules |
| B3 | [WORKER_B3.md](./WORKER_B3.md) | `smoke_compose.sh` optional streaming line |

## Lead duties

1. Workers **B1 → B2 → B3** (B2 may be folded into B1 if one test file suffices—**you** decide, document in PR).  
2. Confirm `pytest -m "not integration"` still excludes new tests (`pytestmark = integration` on module or test).  
3. Document new env vars in `TESTING_NOTES.md` if any (reuse `AEGISLLM_LIVE_OLLAMA=1` + `AEGISLLM_GUARD_BASE_URL` unless a new flag is strictly needed).

## Out of scope

Playwright, Open WebUI UI — **Tier C**.
