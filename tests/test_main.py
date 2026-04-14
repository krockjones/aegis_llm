from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]


def _subprocess_env(**overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("AEGISLLM_CONFIG", None)
    env["PYTHONPATH"] = str(SERVICE_ROOT) + os.pathsep + env.get("PYTHONPATH", "").strip(os.pathsep)
    env.update(overrides)
    return env


def test_main_exits_2_on_invalid_listen_port() -> None:
    """Process entrypoint: invalid env → SystemExit 2 and stderr message (P0 gap)."""
    env = _subprocess_env(
        AEGISLLM_LISTEN_PORT="not_a_port",
        AEGISLLM_LISTEN_HOST="127.0.0.1",
        AEGISLLM_UPSTREAM_BASE_URL="http://127.0.0.1:11434",
    )
    r = subprocess.run(
        [sys.executable, "-c", "from aegis_llm.main import main; main()"],
        cwd=str(SERVICE_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 2, (r.stderr, r.stdout)
    assert "AegisLLM configuration error" in r.stderr


def test_main_success_ordering_and_uvicorn_call(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """main() prints diagnostics then listening line; uvicorn.run is invoked (mocked)."""
    monkeypatch.delenv("AEGISLLM_CONFIG", raising=False)
    monkeypatch.setenv("AEGISLLM_LISTEN_HOST", "127.0.0.1")
    monkeypatch.setenv("AEGISLLM_LISTEN_PORT", "8765")
    monkeypatch.setenv("AEGISLLM_UPSTREAM_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.delenv("AEGISLLM_API_KEYS", raising=False)

    import aegis_llm.main as main_mod

    with patch("uvicorn.run") as mock_run:
        main_mod.main()

    err = capsys.readouterr().err
    assert "product=AegisLLM_Guard" in err
    assert err.index("product=AegisLLM_Guard") < err.index("AegisLLM Guard listening on http://127.0.0.1:8765")
    assert "level=WARNING" not in err
    mock_run.assert_called_once()


def test_main_emits_deployment_warning_wide_bind_no_keys(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("AEGISLLM_CONFIG", raising=False)
    monkeypatch.setenv("AEGISLLM_LISTEN_HOST", "0.0.0.0")
    monkeypatch.setenv("AEGISLLM_LISTEN_PORT", "8765")
    monkeypatch.setenv("AEGISLLM_UPSTREAM_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.delenv("AEGISLLM_API_KEYS", raising=False)

    import aegis_llm.main as main_mod

    with patch("uvicorn.run"):
        main_mod.main()

    err = capsys.readouterr().err
    assert "level=WARNING" in err
    assert "/v1/*" in err
    assert "product=AegisLLM_Guard" in err
    assert err.index("product=AegisLLM_Guard") < err.index("level=WARNING")
