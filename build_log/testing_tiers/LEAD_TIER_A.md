# Tier A lead — mocked upstream (respx) streaming

**You are the Tier A lead sub-agent.** Own **all** Tier A context and keep workers on track.

## Context bundle (read first)

- [TESTING_NOTES.md](../TESTING_NOTES.md) — Tier A row  
- [PLAN_ITERATION_03C_TESTS.md](../PLAN_ITERATION_03C_TESTS.md)  
- `tests/test_chat.py`, `tests/test_hardening.py`, `tests/conftest.py`  
- [SCENARIO_COVERAGE.md](../SCENARIO_COVERAGE.md) — SSE row  

## Team (N = 3)

| Worker | File | Focus |
|--------|------|--------|
| A1 | [WORKER_A1.md](./WORKER_A1.md) | Stream happy-path markers / docstrings |
| A2 | [WORKER_A2.md](./WORKER_A2.md) | Stream error-path (`upstream_http_error`) traceability |
| A3 | [WORKER_A3.md](./WORKER_A3.md) | Scenario table sync for Tier A tests |

## Lead duties

1. Run workers **A1 → A2 → A3** (yourself in one session **or** delegate N Tasks—merge conflicts are your problem).  
2. Run `uv run pytest tests/test_chat.py tests/test_hardening.py -q` (stream-related tests).  
3. Single coherent PR/commit message for Tier A.

## Out of scope

Real Ollama, Docker, Playwright — **Tier B / C**.
