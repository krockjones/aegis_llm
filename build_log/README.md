# Build log

Planning and iteration notes for AegisLLM Guard (wedge roadmap, critiques distilled into shippable passes). Not runtime documentation for operators—see the service **README.md** and **docs/** for that. Older files here may still mention historical monorepo paths; this folder is **candidates for archival** outside the main repo when you trim checkout size—behavior truth remains under **README.md**, **docs/API_CONTRACT.md**, and **docs/SECURITY_POSTURE.md**.

| File | Purpose |
|------|---------|
| [ITERATIONS.md](./ITERATIONS.md) | Ordered iteration plan: core focus, deliverables, and guardrails per pass |
| [PLAN_ITERATION_01.md](./PLAN_ITERATION_01.md) | Executable plan for **Iteration 1** (declared API contract) |
| [PLAN_ITERATION_02.md](./PLAN_ITERATION_02.md) | Executable plan for **Iteration 2** (deployment posture: startup warnings + README defaults matrix) |
| [TESTING_NOTES.md](./TESTING_NOTES.md) | Test pyramid, opt-in live Ollama checks, CI marker notes |
| [SCENARIO_COVERAGE.md](./SCENARIO_COVERAGE.md) | Product scenarios → tests → optional live steps; optional `scenario` pytest mark |
