from __future__ import annotations

import sys


def main() -> None:
    import uvicorn

    from aegis_llm.app import create_app
    from aegis_llm.config import SettingsError, load_settings
    from aegis_llm.diagnostics import (
        log_startup_security_warnings_if_needed,
        print_startup_diagnostics,
    )
    from aegis_llm.logging_setup import setup_logging

    try:
        s = load_settings()
    except SettingsError as e:
        print(f"AegisLLM configuration error: {e}", file=sys.stderr, flush=True)
        raise SystemExit(2) from e

    setup_logging(s.log_level)
    print_startup_diagnostics(s)
    log_startup_security_warnings_if_needed(s)
    print(
        f"AegisLLM Guard listening on http://{s.listen_host}:{s.listen_port}",
        file=sys.stderr,
        flush=True,
    )
    uvicorn.run(
        create_app(s),
        host=s.listen_host,
        port=s.listen_port,
        log_level=s.log_level.lower(),
        access_log=False,
    )


if __name__ == "__main__":
    main()
