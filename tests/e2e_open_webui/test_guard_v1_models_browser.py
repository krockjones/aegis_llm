"""Tier C: Guard ``GET /v1/models`` JSON in Chromium (OpenAI-shaped list)."""

from __future__ import annotations

import os

import pytest


@pytest.mark.open_webui_e2e
@pytest.mark.scenario("guard-v1-models-browser")
def test_guard_v1_models_opens_ai_list_shape(chromium_browser: object) -> None:
    """Navigate to ``/v1/models`` and assert ``200`` + ``{object, data}`` list.

    ``data`` may be empty when Ollama has no tags yet — still a valid regression
    guard against HTML error pages or wrong content-type.
    """
    from playwright.sync_api import Browser

    guard = os.environ.get("AEGISLLM_GUARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    browser = chromium_browser
    assert isinstance(browser, Browser)
    tok = os.environ.get("AEGISLLM_E2E_BEARER", "").strip()
    ctx_kwargs: dict = {}
    if tok:
        ctx_kwargs["extra_http_headers"] = {"Authorization": f"Bearer {tok}"}
    context = browser.new_context(**ctx_kwargs)
    page = context.new_page()
    try:
        resp = page.goto(f"{guard}/v1/models", wait_until="commit", timeout=30_000)
        assert resp is not None
        if resp.status in (401, 403):
            pytest.skip(
                "Guard requires API key for /v1/models — export AEGISLLM_E2E_BEARER to match "
                "AEGISLLM_API_KEYS or run Tier C with keys disabled"
            )
        assert resp.ok, f"unexpected /v1/models status {resp.status}"
        ctype = (resp.headers.get("content-type") or "").lower()
        assert "application/json" in ctype, f"expected JSON content-type, got {ctype!r}"
        data = resp.json()
    finally:
        page.close()
        context.close()

    assert data.get("object") == "list", f"unexpected object field: {data!r}"
    assert isinstance(data.get("data"), list), f"expected data array, got {data!r}"
