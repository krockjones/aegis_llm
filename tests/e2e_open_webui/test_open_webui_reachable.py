"""Minimal Tier C smoke: Open WebUI serves a page when the stack is up."""

from __future__ import annotations

import os

import pytest


@pytest.mark.open_webui_e2e
@pytest.mark.scenario("open-webui-reachable")
def test_open_webui_root_loads(chromium_browser: object) -> None:
    """Hit Open WebUI root URL and assert the SPA shell rendered something meaningful.

    ``OPEN_WEBUI_BASE_URL`` defaults to ``http://127.0.0.1:3000`` (host port from
    ``docker compose --profile tier-c``).
    """
    from playwright.sync_api import Browser

    base = os.environ.get("OPEN_WEBUI_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
    browser = chromium_browser
    assert isinstance(browser, Browser)
    page = browser.new_page()
    try:
        page.goto(base, wait_until="domcontentloaded", timeout=60_000)
        html = page.content()
    finally:
        page.close()

    assert len(html) > 800, "expected a non-trivial HTML document from Open WebUI"
    lowered = html.lower()
    assert "open" in lowered or "webui" in lowered or "sign" in lowered, (
        "expected recognizable Open WebUI shell text in HTML (title, brand, or sign-in)"
    )
