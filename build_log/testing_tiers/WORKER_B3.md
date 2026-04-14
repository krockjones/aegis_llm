# Tier B — Worker B3 (compose smoke streaming)

**Owner:** Tier B lead.

## Scope

- `scripts/smoke_compose.sh` — after models JSON check, add optional **`curl -N`** (or `curl` with `--no-buffer`) **POST** streaming smoke **only if** `curl` supports it in CI; keep script **bash** portable.  
- If streaming in shell is too brittle, add a **comment + TODO** and instead document “run live pytest stream test” in script header—**lead decides** one outcome.

## Acceptance

- [ ] Default `bash scripts/smoke_compose.sh` still exits 0 without extra deps.  
- [ ] If stream line added: failure prints useful log tail.
