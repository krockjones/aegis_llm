# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Removed

- **`build_log/`** and all planning / tier-hub markdown under it (ephemeral agent working notes). Use **CHANGELOG**, **README**, **`docs/`**, and **`tests/`** for product and testing orientation.

### Added

- **QA:** **`tests/test_auth.py`** — `POST /v1/chat/completions` returns **401** without Bearer and **403** with a wrong key when API keys are configured; bearer **200** non-stream smoke. **`tests/test_integration_live.py`** — **`test_live_guard_embeddings_roundtrip`** (opt-in) and shared **`AEGISLLM_LIVE_BEARER`** header helper for live **`/v1/models`**, streaming chat, and embeddings.
- **`docs/SECURITY_POSTURE.md`**: operator-facing risks, mitigations, and how startup WARNING logs relate to bind posture and `AEGISLLM_LOG_LEVEL`.
- **GitHub Actions** **`.github/workflows/aegis-llm.yml`**: pytest matrix on Python **3.10 / 3.12 / 3.13** (`-m "not integration and not open_webui_e2e"`) and a **`compose-smoke`** job running **`scripts/smoke_compose.sh`**.

### Changed

- **Startup security signals:** `main()` calls **`setup_logging`** before posture checks. **`log_startup_security_warnings_if_needed`** emits structured **`level=WARNING`** logs (via `aegis_llm.diagnostics`) when **`/v1/*` is unauthenticated** on a **non-loopback-only** bind (`127.0.0.1` / `::1` are treated as safe), and a separate WARNING when the bind is not loopback-only for **permissive CORS** (wildcard origins in code). Replaces the previous plain-stderr `WARNING:` line for wide-bind-only cases.
- **Documentation** is **standalone-repo-first** (clone root paths); optional upstream monorepo product docs are called out as external.
- **Tests:** **`tests/test_security_posture_warnings.py`** — predicates (`is_loopback_only_bind`, `should_warn_unauthenticated_v1_exposure`), parametrized **`log_startup_security_warnings_if_needed`** (counts, message snippets, ordering, whitespace `::1`), in-process suppression when **`setup_logging("ERROR")`**, and subprocess **`main()`** cases (loopback silence, `AEGISLLM_LOG_LEVEL=ERROR`, dual warnings, CORS-only with keys). **`main()`** in-process stderr assertions remain in **`tests/test_main.py`**.

## [0.2.0] — 2026

Initial packaged release line aligned with `aegis_llm.version.__version__` (OpenAI-compatible Ollama gateway: timeouts, health, optional API keys, request IDs, `/v1/embeddings`, structured logs). Earlier changes are not itemized here.
