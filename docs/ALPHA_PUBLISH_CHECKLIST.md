# Alpha publish checklist (quiet public GitHub)

Use this before tagging or announcing a **public alpha**. Check boxes as you complete each item.

## Must do

- [ ] **README first screen:** a stranger sees **what it is**, **sits in front of Ollama**, **problem**, **what it is not**, **alpha status** without scrolling far — verify [README.md](../README.md) top sections.
- [ ] **One canonical path:** Path A (Docker Compose) is the obvious first run; [GETTING_STARTED.md](./GETTING_STARTED.md) Path A matches.
- [ ] **Alpha boundary:** [README.md](../README.md) “Alpha release scope” table still matches [API_CONTRACT.md](./API_CONTRACT.md) out-of-scope language.
- [ ] **Public-copy pass:** no accidental “universal gateway / full parity / multi-backend platform” **claims** (negations in “what it is not” are fine).
- [ ] **Smoke commands run** (record date / machine in a private note if useful):
  - [ ] `pytest tests/ -q -m "not integration and not open_webui_e2e"` — **Last run:** ______ (expect: all pass; CI uses the same filter.)
  - [ ] **Path A quickstart:** from repo root, `docker compose up --build`, pull a model, `curl` `/healthz`, `/readyz`, one chat — **Last run:** ______
  - [ ] **`bash examples/curl_examples.sh`** — requires **`jq`** and a **reachable Guard** at `AEGISLLM_EXAMPLE_BASE` (default `http://127.0.0.1:8765`). **Last run:** ______
  - [ ] (Optional) `AEGISLLM_LIVE_OLLAMA=1 pytest tests/ -q -m "not open_webui_e2e"` with real Ollama + Guard.

## Should do

- [ ] **Doc roles:** README = wedge + fastest path; GETTING_STARTED = setup; API_CONTRACT = surface; SECURITY_POSTURE = deployment truth; INTEGRATION_OPEN_WEBUI = client notes — no duplicate “what is Guard” essays.
- [ ] **Community one-liner** in README still accurate after edits.
- [ ] **Metadata:** [pyproject.toml](../pyproject.toml) license/description (Apache-2.0 + [LICENSE](../LICENSE)); [.gitignore](../.gitignore); no committed secrets; internal links work.
- [ ] **Tests section** in README states what default pytest does **and does not** prove.
- [ ] **Security wording:** README + [SECURITY_POSTURE.md](./SECURITY_POSTURE.md) agree on public routes, keys, CORS, warnings vs enforcement.

## Nice to do

- [ ] One terminal transcript or screenshot in README (optional).
- [ ] Short outreach list (private).

## Go / hold

**Publish when:**

- [ ] A stranger can understand the repo quickly from the README.
- [ ] The main path is obvious (Compose Path A).
- [ ] README does not overclaim relative to code + API_CONTRACT.
- [ ] Docs agree with each other on scope and security.
- [ ] Default tests + at least one manual smoke path have been run recently.

**Hold if:**

- [ ] Main path is still ambiguous.
- [ ] The repo story reads broader than the implementation.
- [ ] You are waiting for “one more polish” to answer market fit (ship the alpha and listen instead).
