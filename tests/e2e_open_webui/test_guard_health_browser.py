"""Tier C: Guard /healthz reachable from the same Playwright stack as Open WebUI tests."""

from __future__ import annotations

import os

import pytest


@pytest.mark.open_webui_e2e
@pytest.mark.scenario("guard-health-browser")
def test_guard_healthz_json_ok(chromium_browser: object) -> None:
    """Load Guard ``/healthz`` in Chromium and assert JSON ``{"status": "ok"}``.

    Uses ``AEGISLLM_GUARD_BASE_URL`` (default ``http://127.0.0.1:8765``), same as
    live integration docs — host origin only, no ``/v1`` suffix.
    """
    from playwright.sync_api import Browser

    guard = os.environ.get("AEGISLLM_GUARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    browser = chromium_browser
    assert isinstance(browser, Browser)
    page = browser.new_page()
    try:
        resp = page.goto(f"{guard}/healthz", wait_until="commit", timeout=30_000)
        assert resp is not None, "expected a navigation response from /healthz"
        assert resp.ok, f"unexpected HTTP status from /healthz: {resp.status}"
        data = resp.json()
    finally:
        page.close()

    assert data.get("status") == "ok", f"unexpected /healthz payload: {data!r}"
