"""Tier C: Guard /readyz reachable in Chromium (same stack as Open WebUI E2E)."""

from __future__ import annotations

import os

import pytest


@pytest.mark.open_webui_e2e
@pytest.mark.scenario("guard-readyz-browser")
def test_guard_readyz_json_shape(chromium_browser: object) -> None:
    """Load ``GET /readyz`` in the browser and assert a JSON backend health payload.

    Accepts ``200`` (``status: ready``) or ``503`` (``status: not_ready``) while
    Ollama is warming — both are valid Guard responses.
    """
    from playwright.sync_api import Browser

    guard = os.environ.get("AEGISLLM_GUARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    browser = chromium_browser
    assert isinstance(browser, Browser)
    page = browser.new_page()
    try:
        resp = page.goto(f"{guard}/readyz", wait_until="commit", timeout=30_000)
        assert resp is not None, "expected navigation response"
        assert resp.status in (200, 503), f"unexpected /readyz status {resp.status}"
        data = resp.json()
    finally:
        page.close()

    assert data.get("status") in ("ready", "not_ready"), f"unexpected /readyz body: {data!r}"
    assert data.get("backend") == "ollama", f"expected backend ollama, got {data!r}"
