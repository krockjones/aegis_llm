# Tier A — Worker A2 (stream upstream HTTP error)

**Owner:** Tier A lead.

## Scope

- `tests/test_hardening.py` — `test_chat_stream_upstream_http_error`  
- Add `@pytest.mark.scenario("chat-stream-sse-error")` **if** not redundant with existing marks; otherwise strengthen docstring only.

## Acceptance

- [ ] Scenario id appears in [SCENARIO_COVERAGE.md](../SCENARIO_COVERAGE.md) SSE row **or** docstring explains sharing `chat-stream-sse` family.  
- [ ] `uv run pytest tests/test_hardening.py::test_chat_stream_upstream_http_error -q` passes.
