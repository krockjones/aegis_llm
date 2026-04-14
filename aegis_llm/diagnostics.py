from __future__ import annotations

import sys

from aegis_llm.config import Settings
from aegis_llm.logging_setup import get_logger
from aegis_llm.version import __version__

_log = get_logger("diagnostics")

# Binds treated as loopback-only for exposure warnings (no /v1 auth required for local-only).
_LOOPBACK_ONLY_BINDS = frozenset({"127.0.0.1", "::1"})


def _normalized_listen_host(host: str) -> str:
    return host.strip()


def is_loopback_only_bind(s: Settings) -> bool:
    """True when Guard listens only on loopback addresses."""
    return _normalized_listen_host(s.listen_host) in _LOOPBACK_ONLY_BINDS


def should_warn_unauthenticated_v1_exposure(s: Settings) -> bool:
    """True when /v1/* has no Bearer requirement and bind is not loopback-only."""
    if s.api_keys:
        return False
    return not is_loopback_only_bind(s)


def log_startup_security_warnings_if_needed(s: Settings) -> None:
    """Emit structured WARNING logs for risky default posture (after setup_logging in main)."""
    if should_warn_unauthenticated_v1_exposure(s):
        _log.warning(
            "/v1/* is reachable without authentication (non-loopback bind, no api_keys). "
            "Paths /healthz, /readyz, /docs, /openapi.json, /redoc remain public by design; "
            "see README (Security / deployment) and docs/SECURITY_POSTURE.md."
        )
    if not is_loopback_only_bind(s):
        _log.warning(
            "CORS allow_origins is wildcard in app code while bound beyond loopback; "
            "browser origins can reach network-exposed routes—terminate with a reverse proxy "
            "for stricter CORS if needed. See docs/SECURITY_POSTURE.md."
        )


def print_startup_diagnostics(s: Settings) -> None:
    """Structured one-shot summary for operators (stderr)."""
    auth = "yes" if s.api_keys else "no"
    lic = "yes" if s.license_key_placeholder else "no"
    line = (
        f"product=AegisLLM_Guard version={__version__} "
        f"backend={s.backend_type} "
        f"bind={s.listen_host}:{s.listen_port} "
        f"upstream_base_url={s.upstream_base_url} "
        f"auth={auth} "
        f"timeouts_connect_s={s.connect_timeout} timeouts_read_s={s.read_timeout} "
        f"log_level={s.log_level} "
        f"license_key_set={lic}"
    )
    print(line, file=sys.stderr, flush=True)
