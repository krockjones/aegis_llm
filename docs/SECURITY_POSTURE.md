# Operator security posture — AegisLLM Guard

This document complements the README **Security / deployment** table and [API_CONTRACT.md](./API_CONTRACT.md). It lists **risks** from default and common configurations, **mitigations**, and what Guard emits at startup.

---

## Trust boundaries

| Boundary | Risk if mishandled |
|----------|-------------------|
| **Listen address** | Binding beyond `127.0.0.1` / `::1` exposes the HTTP surface to the reachable network (LAN, container network, or Internet if the port is published). |
| **`AEGISLLM_API_KEYS`** | Empty keys mean **`/v1/*` is unauthenticated** for any caller that can reach the port. |
| **Public by design** | Even with keys set, **`/`**, **`/healthz`**, **`/readyz`**, **`/docs`**, **`/openapi.json`**, **`/redoc`** do not require Bearer tokens. Do not expose these unintentionally on hostile networks without a proxy or firewall policy. |
| **Upstream URL** | `AEGISLLM_UPSTREAM_BASE_URL` (and legacy `AEGISLLM_OLLAMA_BASE_URL`) is a **relay target**. Point it only at intended Ollama instances; misconfiguration can forward traffic toward unintended hosts from Guard’s network position. |
| **Response headers** | `GET /v1/models` may include **`X-AegisLLM-Upstream-Base`**, disclosing the configured upstream to any client that can call that route. Strip at a reverse proxy if undesirable. |

---

## Fixed product choices (today)

| Behavior | Notes | Mitigation |
|----------|--------|------------|
| **CORS `allow_origins=["*"]`** | Set in application code; not env-tunable. | Put Guard behind a reverse proxy that enforces origin policy, or change code for your deployment. |
| **Structured access logs** | May include paths and status; useful for ops, sensitive in shared log stores. | Restrict log aggregation access; tune retention. |

---

## Startup diagnostics and warnings

1. **Diagnostics line** (stderr, plain text): one line with `product=`, `bind=`, `upstream_base_url=`, `auth=`, timeouts, and `log_level=`. Always emitted when `main()` starts successfully.

2. **Structured WARNING logs** (stderr, `level=WARNING` via `aegis_llm` logger) when posture is lax:
   - **Unauthenticated `/v1/*`:** emitted when **`AEGISLLM_API_KEYS` is empty** and the bind address is **not** loopback-only (`127.0.0.1` or `::1`). This includes `0.0.0.0`, `::`, explicit LAN IPs, and hostnames such as `localhost` (not treated as loopback-only for this check—use numeric loopback for strict local-only binding).
   - **Permissive CORS on a non-loopback bind:** emitted whenever the bind is not loopback-only, **including** when API keys are set—keys do not tighten CORS.

If `AEGISLLM_LOG_LEVEL` is set to **`ERROR`** or higher, WARNING lines are suppressed by the logging configuration (by design).

**Regression tests:** `tests/test_security_posture_warnings.py` (predicates, log counts, message ordering, log-level suppression, and subprocess `main()` with mocked `uvicorn.run`).

---

## Recommended mitigations (short)

- **Production / LAN:** set **`AEGISLLM_API_KEYS`**, bind only behind a **firewall or LB**, and use **mTLS / proxy auth** where appropriate.
- **Local dev:** default **`127.0.0.1`** bind and optional keys are usually sufficient.
- **CORS / docs exposure:** front Guard with **nginx**, **Envoy**, or cloud LB rules if browsers or attackers must not reach OpenAPI or wildcard CORS.

---

## Related documentation

- [README.md](../README.md) — env reference, compose, curl examples  
- [API_CONTRACT.md](./API_CONTRACT.md) — authenticated vs public routes  
- [GETTING_STARTED.md](./GETTING_STARTED.md) — first-run paths  
