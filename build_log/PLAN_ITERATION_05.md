# Plan: Iteration 5 — Abstraction hygiene (internal only)

**Parent:** [ITERATIONS.md](./ITERATIONS.md) · **Iteration 5**  
**Goal:** Keep the **backend boundary** useful for structure and tests **without** implying a multi-backend product. **No second backend** in this iteration.

---

## 1. Objective

| Outcome | Notes |
|---------|--------|
| **`Backend` protocol** | Reflects every method routes call today, including `health_probe` for `/readyz`. |
| **Honest copy** | Package and factory docstrings do not read like a vLLM/LM Studio roadmap. |
| **Typing** | `create_backend` returns `Backend`; runtime remains `OllamaBackend` only. |
| **Product language** | Canonical positioning stays in [README.md](../README.md) and [docs/API_CONTRACT.md](../docs/API_CONTRACT.md) § *Backends*; this plan tracks code alignment only. |

---

## 2. Non-goals

- Adding another upstream adapter, feature flags for “vendor pick”, or dependencies to justify the factory.
- Changing `/readyz` behavior, Ollama URLs, or error payloads except via typing-only edits (none expected).

---

## 3. Done when

- [x] `Backend` declares `health_probe`; `OllamaBackend` satisfies the protocol.
- [x] `aegis_llm/backends/__init__.py` and `factory.py` docstrings state Ollama-only production and internal protocol purpose.
- [x] `create_backend` is annotated `-> Backend`.
- [x] This file exists and verification below has been run after merge.

---

## 4. Verification

From `zed_toolkit/services/aegis_llm`:

```bash
python -m pytest tests/test_health.py tests/test_hardening.py::test_create_backend_rejects_unknown_type -q
```

---

## 5. Code touch list (this pass)

| Path | Change |
|------|--------|
| `aegis_llm/backends/base.py` | Add `health_probe` to `Backend`. |
| `aegis_llm/backends/__init__.py` | Module docstring: Ollama-only, internal boundary. |
| `aegis_llm/backends/factory.py` | Module + `create_backend` docstrings; `-> Backend`. |

---

## 6. Handoff

Future adapters belong behind the same protocol **only** when a concrete wedge customer exists; until then, docs and factory should keep “Ollama only” explicit.
