# Tier B — Worker B2 (model id + auth skip)

**Owner:** Tier B lead.

## Scope

- Live stream test must **`GET /v1/models`** first; pick `data[0]["id"]` (skip if empty).  
- If response is **401/403**, `pytest.skip` with message to set Bearer when `AEGISLLM_API_KEYS` configured (document in docstring).

## Acceptance

- [ ] No magic model string required for green local run.  
- [ ] Docstring lists env vars.
