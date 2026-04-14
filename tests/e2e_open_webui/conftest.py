"""Tier C — Open WebUI browser E2E (Playwright).

Tests are marked ``open_webui_e2e`` and excluded from default CI via
``pytest -m "not open_webui_e2e"``.

Set ``AEGISLLM_OPEN_WEBUI_E2E=1`` and install ``.[e2e]`` + ``python -m playwright install`` before running.
"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest

pytestmark = pytest.mark.open_webui_e2e


def _launch_chromium_headless(playwright: object) -> object:
    """Return a launched Chromium browser; fail with an install hint if binaries are missing."""
    try:
        return playwright.chromium.launch(headless=True)  # type: ignore[union-attr]
    except Exception as e:
        err = str(e)
        if "Executable doesn't exist" in err and "chromium_headless_shell" in err:
            pytest.fail(
                "Playwright cannot find the Chrome Headless Shell bundle "
                "(no chromium_headless_shell-* under the browser cache; "
                "`chromium.launch(headless=True)` requires it on recent Playwright). "
                "From this same virtualenv run:\n\n"
                "  python -m playwright install\n\n"
                "Avoid relying on `playwright install chromium` alone for Tier C — it can "
                "leave headless_shell uninstalled while older chromium-* folders remain.\n\n"
                f"Driver error:\n{err}"
            )
        raise


@pytest.fixture
def chromium_browser() -> Generator[object, None, None]:
    """One headless Chromium instance per test (Tier C shared launcher)."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = _launch_chromium_headless(p)
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture(autouse=True)
def _require_open_webui_e2e_flag() -> None:
    if os.environ.get("AEGISLLM_OPEN_WEBUI_E2E") != "1":
        pytest.skip(
            "Tier C Open WebUI E2E disabled. Set AEGISLLM_OPEN_WEBUI_E2E=1, install .[e2e], "
            "and run `python -m playwright install`."
        )
