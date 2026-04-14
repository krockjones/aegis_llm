# Tier A — Worker A1 (stream happy path)

**Owner:** Tier A lead.

## Scope

- `tests/test_chat.py` — `test_chat_completions_stream`  
- Ensure `@pytest.mark.scenario("chat-stream-sse")` remains; add/refresh **docstring** tying test to Tier A / `SCENARIO_COVERAGE`.

## Acceptance

- [ ] Docstring mentions mocked NDJSON → SSE + `[DONE]` (Tier A).  
- [ ] No change to assertion semantics unless fixing a bug.
