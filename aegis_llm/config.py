from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class SettingsError(ValueError):
    """Invalid configuration (env, YAML, or types)."""


def _env_str(key: str, default: str) -> str:
    v = os.environ.get(key)
    return v.strip() if v and v.strip() else default


def _env_int(key: str, default: int) -> int:
    v = os.environ.get(key)
    if v is None or not str(v).strip():
        return default
    try:
        return int(str(v).strip())
    except ValueError as e:
        raise SettingsError(f"Invalid integer for {key}: {v!r}") from e


def _env_float(key: str, default: float) -> float:
    v = os.environ.get(key)
    if v is None or not str(v).strip():
        return default
    try:
        return float(str(v).strip())
    except ValueError as e:
        raise SettingsError(f"Invalid float for {key}: {v!r}") from e


def _parse_api_keys(raw: str | None) -> tuple[str, ...]:
    if not raw or not raw.strip():
        return ()
    return tuple(k.strip() for k in raw.split(",") if k.strip())


def _coerce_int(value: Any, *, ctx: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise SettingsError(f"Invalid integer for {ctx}: {value!r}") from e


def _coerce_float(value: Any, *, ctx: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as e:
        raise SettingsError(f"Invalid float for {ctx}: {value!r}") from e


@dataclass(frozen=True)
class Settings:
    """Runtime configuration (honest naming: backend + upstream, not 'generic mesh' yet)."""

    backend_type: str
    upstream_base_url: str
    listen_host: str
    listen_port: int
    api_keys: tuple[str, ...]
    connect_timeout: float
    read_timeout: float
    log_level: str
    license_key_placeholder: str | None = None

    def upstream_timeout(self) -> Any:
        import httpx

        return httpx.Timeout(
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=self.connect_timeout,
            pool=self.connect_timeout,
        )


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dict(out[k], v)  # type: ignore[arg-type]
        else:
            out[k] = v
    return out


def _load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_settings() -> Settings:
    """Load settings from environment, optionally merged with YAML at AEGISLLM_CONFIG."""
    cfg_path = os.environ.get("AEGISLLM_CONFIG")
    file_cfg: dict[str, Any] = {}
    if cfg_path:
        file_cfg = _load_yaml_config(Path(cfg_path))

    backend_type = str(file_cfg.get("backend", _env_str("AEGISLLM_BACKEND", "ollama"))).strip().lower()
    if not backend_type:
        raise SettingsError("backend / AEGISLLM_BACKEND must not be empty")

    # Upstream URL: generic key first, then legacy Ollama-specific env/YAML for compatibility.
    upstream_raw = file_cfg.get("upstream_base_url")
    if upstream_raw is None:
        upstream_raw = file_cfg.get("ollama_base_url")
    if upstream_raw is None:
        upstream_raw = _env_str(
            "AEGISLLM_UPSTREAM_BASE_URL",
            _env_str("AEGISLLM_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        )
    upstream_base_url = str(upstream_raw).rstrip("/")
    if not (
        upstream_base_url.startswith("http://") or upstream_base_url.startswith("https://")
    ):
        raise SettingsError(
            "upstream_base_url must start with http:// or https:// "
            f"(got {upstream_base_url!r})"
        )

    listen_host_raw = file_cfg.get("listen_host")
    if listen_host_raw is None:
        listen_host = _env_str("AEGISLLM_LISTEN_HOST", "127.0.0.1")
    else:
        listen_host = str(listen_host_raw).strip()
        if not listen_host:
            listen_host = _env_str("AEGISLLM_LISTEN_HOST", "127.0.0.1")
    listen_port = _coerce_int(
        file_cfg.get("listen_port", _env_int("AEGISLLM_LISTEN_PORT", 8765)),
        ctx="listen_port / AEGISLLM_LISTEN_PORT",
    )

    keys_from_file = file_cfg.get("api_keys")
    if isinstance(keys_from_file, list):
        api_keys = tuple(str(x).strip() for x in keys_from_file if str(x).strip())
    else:
        api_keys = _parse_api_keys(os.environ.get("AEGISLLM_API_KEYS"))

    timeouts = file_cfg.get("timeouts")
    if isinstance(timeouts, dict):
        connect_timeout = _coerce_float(
            timeouts.get("connect", _env_float("AEGISLLM_CONNECT_TIMEOUT", 5.0)),
            ctx="timeouts.connect",
        )
        read_timeout = _coerce_float(
            timeouts.get("read", _env_float("AEGISLLM_READ_TIMEOUT", 300.0)),
            ctx="timeouts.read",
        )
    else:
        connect_timeout = _env_float("AEGISLLM_CONNECT_TIMEOUT", 5.0)
        read_timeout = _env_float("AEGISLLM_READ_TIMEOUT", 300.0)

    log_level = str(file_cfg.get("log_level", _env_str("AEGISLLM_LOG_LEVEL", "INFO"))).upper()
    lic = os.environ.get("AEGISLLM_LICENSE_KEY")
    license_key_placeholder = lic.strip() if lic and lic.strip() else None

    return Settings(
        backend_type=backend_type,
        upstream_base_url=upstream_base_url,
        listen_host=listen_host,
        listen_port=listen_port,
        api_keys=api_keys,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        log_level=log_level,
        license_key_placeholder=license_key_placeholder,
    )
