# Tier B — Worker B1 (live streaming POST)

**Owner:** Tier B lead.

## Scope

- Add **`test_live_guard_chat_completion_stream`** (name may vary) in `tests/test_integration_live.py` **or** a new `tests/test_integration_live_stream.py` re-exporting same `pytestmark`.  
- **Gated:** same as existing live tests — `AEGISLLM_LIVE_OLLAMA=1`; skip on connect / `503` `/readyz`.  
- **POST** `f"{guard}/v1/chat/completions"` with `{"model": <id>, "messages": [{"role":"user","content":"Say hi in a few words."}], "stream": true}`.  
- Read response body (stream); assert **`chat.completion.chunk`** and **`[DONE]`** appear; assert `text/event-stream` content-type if header present.

## Acceptance

- [ ] `@pytest.mark.integration` (or module-level `pytestmark`).  
- [ ] No hard dependency when env unset (skip).  
- [ ] Reasonable timeout (Ollama can be slow).
