"""Startup security posture (point 5): loopback vs exposure, API keys, CORS warnings, log level, ordering."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from aegis_llm.config import Settings
from aegis_llm.diagnostics import (
    is_loopback_only_bind,
    log_startup_security_warnings_if_needed,
    should_warn_unauthenticated_v1_exposure,
)
from aegis_llm.logging_setup import setup_logging

SERVICE_ROOT = Path(__file__).resolve().parents[1]

_UNAUTH_SNIP = "/v1/*"
_CORS_SNIP = "CORS allow_origins"


@pytest.fixture
def aegis_caplog(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture aegis_llm.* logs (tree does not propagate to root)."""
    setup_logging("INFO")
    lg = logging.getLogger("aegis_llm")
    caplog.set_level(logging.DEBUG, logger="aegis_llm")
    lg.addHandler(caplog.handler)
    yield caplog
    lg.removeHandler(caplog.handler)


def _settings(
    *,
    listen_host: str,
    api_keys: tuple[str, ...] = (),
    log_level: str = "INFO",
) -> Settings:
    return Settings(
        backend_type="ollama",
        upstream_base_url="http://127.0.0.1:11434",
        listen_host=listen_host,
        listen_port=8765,
        api_keys=api_keys,
        connect_timeout=5.0,
        read_timeout=300.0,
        log_level=log_level,
    )


# --- is_loopback_only_bind (edge: whitespace, non-canonical hosts) ---


@pytest.mark.parametrize(
    ("host", "expected_loopback"),
    [
        ("127.0.0.1", True),
        ("::1", True),
        (" 127.0.0.1 ", True),
        ("  ::1  ", True),
        ("0.0.0.0", False),
        ("::", False),
        ("localhost", False),
        ("192.168.1.10", False),
        ("10.0.0.1", False),
        ("fe80::1", False),
        ("", False),
    ],
)
def test_is_loopback_only_bind(host: str, expected_loopback: bool) -> None:
    s = _settings(listen_host=host)
    assert is_loopback_only_bind(s) is expected_loopback


# --- should_warn_unauthenticated_v1_exposure (predicate; keys edge cases) ---


@pytest.mark.parametrize(
    ("host", "keys", "expected"),
    [
        # Positive: must warn (non-loopback, no keys)
        ("0.0.0.0", (), True),
        ("::", (), True),
        (" 0.0.0.0 ", (), True),
        ("localhost", (), True),
        ("10.0.0.5", (), True),
        ("172.16.0.1", (), True),
        # Negative: loopback or keys set
        ("127.0.0.1", (), False),
        ("::1", (), False),
        ("0.0.0.0", ("secret",), False),
        ("::", ("k",), False),
        ("192.168.0.1", ("k",), False),
        # Edge: any non-empty api_keys tuple counts as "auth configured" (including whitespace-only string)
        ("0.0.0.0", (" ",), False),
        ("0.0.0.0", ("a", "b"), False),
    ],
)
def test_should_warn_unauthenticated_v1_exposure(
    host: str, keys: tuple[str, ...], expected: bool
) -> None:
    s = _settings(listen_host=host, api_keys=keys)
    assert should_warn_unauthenticated_v1_exposure(s) is expected


# --- log_startup_security_warnings_if_needed (integrated messages + order) ---


@pytest.mark.parametrize(
    ("host", "keys", "expected_warn_count", "expect_unauth", "expect_cors"),
    [
        # Silent on loopback-only (positive: safe default)
        ("127.0.0.1", (), 0, False, False),
        ("::1", (), 0, False, False),
        # Dual warning: open /v1 + CORS note
        ("0.0.0.0", (), 2, True, True),
        ("::", (), 2, True, True),
        ("192.168.55.2", (), 2, True, True),
        ("fe80::42", (), 2, True, True),
        # Keys set: CORS only on non-loopback
        ("0.0.0.0", ("token",), 1, False, True),
        ("::", ("x", "y"), 1, False, True),
        ("10.0.0.1", ("k",), 1, False, True),
        # Keys + loopback: silent
        ("127.0.0.1", ("k",), 0, False, False),
        ("::1", ("k",), 0, False, False),
    ],
)
def test_log_startup_security_warnings_parametrized(
    aegis_caplog: pytest.LogCaptureFixture,
    host: str,
    keys: tuple[str, ...],
    expected_warn_count: int,
    expect_unauth: bool,
    expect_cors: bool,
) -> None:
    log_startup_security_warnings_if_needed(_settings(listen_host=host, api_keys=keys))
    warns = [r for r in aegis_caplog.records if r.levelname == "WARNING"]
    assert len(warns) == expected_warn_count
    joined = " ".join(r.message for r in warns)
    assert (_UNAUTH_SNIP in joined) is expect_unauth
    assert (_CORS_SNIP in joined) is expect_cors
    if expect_unauth and expect_cors:
        assert _UNAUTH_SNIP in warns[0].message
        assert _CORS_SNIP in warns[1].message
        assert "SECURITY_POSTURE.md" in warns[0].message and "SECURITY_POSTURE.md" in warns[1].message


def test_log_startup_security_warnings_whitespace_loopback_is_safe(
    aegis_caplog: pytest.LogCaptureFixture,
) -> None:
    """Leading/trailing spaces on ::1 still normalize to loopback-only."""
    log_startup_security_warnings_if_needed(_settings(listen_host="  ::1  "))
    assert not [r for r in aegis_caplog.records if r.levelname == "WARNING"]


def test_log_startup_security_warnings_suppressed_when_logger_level_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """With aegis_llm effective level ERROR, WARNING startup lines are not emitted."""
    setup_logging("ERROR")
    lg = logging.getLogger("aegis_llm")
    # Do not call caplog.set_level here — it would lower the logger and defeat ERROR filtering.
    lg.addHandler(caplog.handler)
    try:
        log_startup_security_warnings_if_needed(_settings(listen_host="0.0.0.0"))
        warns = [r for r in caplog.records if r.levelname == "WARNING"]
        assert warns == []
    finally:
        lg.removeHandler(caplog.handler)


def _subprocess_env(**overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("AEGISLLM_CONFIG", None)
    env["PYTHONPATH"] = str(SERVICE_ROOT) + os.pathsep + env.get("PYTHONPATH", "").strip(os.pathsep)
    env.update(overrides)
    return env


def _run_main_mocked_uvicorn(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    code = (
        "from unittest.mock import patch\n"
        "from aegis_llm.main import main\n"
        "with patch('uvicorn.run'):\n"
        "    main()\n"
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(SERVICE_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_main_subprocess_no_security_warnings_on_loopback() -> None:
    """End-to-end: loopback bind + no keys → no level=WARNING in stderr."""
    env = _subprocess_env(
        AEGISLLM_LISTEN_HOST="127.0.0.1",
        AEGISLLM_LISTEN_PORT="8765",
        AEGISLLM_UPSTREAM_BASE_URL="http://127.0.0.1:11434",
    )
    env.pop("AEGISLLM_API_KEYS", None)
    r = _run_main_mocked_uvicorn(env)
    assert r.returncode == 0, r.stderr
    assert "level=WARNING" not in r.stderr


def test_main_subprocess_no_warnings_on_ipv6_loopback() -> None:
    env = _subprocess_env(
        AEGISLLM_LISTEN_HOST="::1",
        AEGISLLM_LISTEN_PORT="8765",
        AEGISLLM_UPSTREAM_BASE_URL="http://127.0.0.1:11434",
    )
    env.pop("AEGISLLM_API_KEYS", None)
    r = _run_main_mocked_uvicorn(env)
    assert r.returncode == 0, r.stderr
    assert "level=WARNING" not in r.stderr


def test_main_subprocess_security_warnings_suppressed_when_log_level_error() -> None:
    """AEGISLLM_LOG_LEVEL=ERROR: risky bind but WARNING records are filtered out."""
    env = _subprocess_env(
        AEGISLLM_LISTEN_HOST="0.0.0.0",
        AEGISLLM_LISTEN_PORT="8765",
        AEGISLLM_UPSTREAM_BASE_URL="http://127.0.0.1:11434",
        AEGISLLM_LOG_LEVEL="ERROR",
    )
    env.pop("AEGISLLM_API_KEYS", None)
    r = _run_main_mocked_uvicorn(env)
    assert r.returncode == 0, r.stderr
    assert _UNAUTH_SNIP not in r.stderr
    assert _CORS_SNIP not in r.stderr


def test_main_subprocess_dual_warnings_non_loopback_no_keys() -> None:
    env = _subprocess_env(
        AEGISLLM_LISTEN_HOST="0.0.0.0",
        AEGISLLM_LISTEN_PORT="8765",
        AEGISLLM_UPSTREAM_BASE_URL="http://127.0.0.1:11434",
        AEGISLLM_LOG_LEVEL="INFO",
    )
    env.pop("AEGISLLM_API_KEYS", None)
    r = _run_main_mocked_uvicorn(env)
    assert r.returncode == 0, r.stderr
    assert r.stderr.count("level=WARNING") == 2
    assert _UNAUTH_SNIP in r.stderr
    assert _CORS_SNIP in r.stderr


def test_main_subprocess_cors_only_when_api_keys_configured() -> None:
    """Wide bind + keys: /v1 is authenticated; only CORS posture WARNING remains."""
    env = _subprocess_env(
        AEGISLLM_LISTEN_HOST="0.0.0.0",
        AEGISLLM_LISTEN_PORT="8765",
        AEGISLLM_UPSTREAM_BASE_URL="http://127.0.0.1:11434",
        AEGISLLM_LOG_LEVEL="INFO",
        AEGISLLM_API_KEYS="integration-test-key",
    )
    r = _run_main_mocked_uvicorn(env)
    assert r.returncode == 0, r.stderr
    assert r.stderr.count("level=WARNING") == 1
    assert _CORS_SNIP in r.stderr
    assert _UNAUTH_SNIP not in r.stderr
