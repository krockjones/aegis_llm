"""Tier C: Open WebUI triggers a streaming chat completion (SSE) observable from the browser."""

from __future__ import annotations

import os
import platform
import time

import httpx
import pytest


def _dismiss_ephemeral_overlays(page: object) -> None:
    """Best-effort close banners/modals that can cover the composer."""
    from playwright.sync_api import TimeoutError as PWTimeout

    candidates = (
        page.locator('[aria-label="Close"]').first,
        page.locator('button:has-text("Close")').first,
        page.locator('[data-testid="modal-close"]').first,
    )
    for loc in candidates:
        try:
            if loc.is_visible(timeout=400):
                loc.click(timeout=2_000)
                time.sleep(0.25)
        except PWTimeout:
            continue
        except Exception:
            continue


def _try_select_first_model(page: object) -> None:
    """Open WebUI v0.5.x: pick a model when the navbar still shows *Select a model*."""
    trigger = page.get_by_text("Select a model", exact=False)
    if trigger.count() == 0:
        return
    trigger.first.click(timeout=8_000)
    options = page.locator("[role='listbox'] [role='option']")
    if options.count() == 0:
        return
    options.first.click(timeout=15_000)


def _composer(page: object) -> object:
    """Return the live composer (TipTap / ProseMirror: ``#chat-input`` upstream).

    ``MessageInput.svelte`` wraps the input in ``{#if loaded}``; waiting only for
    *visible* can time out while APIs warm up even though the node is already in
    the tree. Prefer *attached*, scroll into view, then optional visible wait.
    """
    from playwright.sync_api import TimeoutError as PWTimeout

    _dismiss_ephemeral_overlays(page)

    try:
        page.wait_for_selector("#chat-input", state="attached", timeout=90_000)
        loc = page.locator("#chat-input").first
    except PWTimeout:
        loc = page.locator("main [contenteditable='true']").first
        try:
            loc.wait_for(state="attached", timeout=20_000)
        except PWTimeout as exc:
            pytest.skip(
                "Open WebUI composer not found (#chat-input or main contenteditable). "
                "Confirm OPEN_WEBUI_BASE_URL is the app root and the session reaches the chat surface. "
                f"(wait timeout: {exc})"
            )

    loc.scroll_into_view_if_needed()
    try:
        loc.wait_for(state="visible", timeout=20_000)
    except PWTimeout:
        pass
    return loc


@pytest.mark.open_webui_e2e
@pytest.mark.scenario("open-webui-stream-network")
def test_open_webui_chat_stream_posts_sse(chromium_browser: object) -> None:
    """Drive the Open WebUI composer so the browser emits a streaming POST.

    Requires at least one model from Guard (``GET /v1/models``). Pull a model in
    Ollama first, e.g. ``docker compose exec ollama ollama pull llama3.2``.

    Open WebUI **v0.5.7** uses **RichTextInput** (ProseMirror): the node with
    ``id="chat-input"`` is not a plain ``<textarea>`` — upstream
    ``MessageInput.svelte`` / ``RichTextInput.svelte``. A model must be selected
    or the UI will not submit (toast: *Please select a model first*).
    """
    from playwright.sync_api import Browser

    guard = os.environ.get("AEGISLLM_GUARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    try:
        mr = httpx.get(f"{guard}/v1/models", timeout=15.0)
        mr.raise_for_status()
        models = (mr.json() or {}).get("data") or []
    except (httpx.HTTPError, ValueError, TypeError):
        pytest.skip("Guard /v1/models unreachable from test host")

    if not models or not isinstance(models[0], dict) or not models[0].get("id"):
        pytest.skip("No models from Guard — pull a model in Ollama (see docker-compose.yml comments)")

    base = os.environ.get("OPEN_WEBUI_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
    browser = chromium_browser
    assert isinstance(browser, Browser)
    page = browser.new_page()

    def _is_chat_completion(resp: object) -> bool:
        req = resp.request
        if req.method != "POST":
            return False
        u = resp.url.lower()
        return "completions" in u and "chat" in u

    try:
        page.goto(base, wait_until="load", timeout=90_000)
        html = page.content().lower()
        if "sign in" in html or "sign up" in html or "create an account" in html:
            pytest.skip("Open WebUI auth gate — configure dev auth or complete signup for Tier C stream")

        _try_select_first_model(page)
        box = _composer(page)
        box.click(timeout=8_000, force=True)
        try:
            box.fill("Reply in exactly three words.", timeout=20_000, force=True)
        except Exception:
            if platform.system() == "Darwin":
                page.keyboard.press("Meta+A")
            else:
                page.keyboard.press("Control+A")
            page.keyboard.type("Reply in exactly three words.", delay=15)

        send = page.locator("#send-message-button")
        with page.expect_response(_is_chat_completion, timeout=120_000) as resp_waiter:
            if send.count() > 0:
                try:
                    if send.is_enabled():
                        send.click()
                    else:
                        box.press("Enter")
                except Exception:
                    box.press("Enter")
            else:
                box.press("Enter")

        resp = resp_waiter.value
        assert resp.ok, f"chat completion HTTP {resp.status}"
        ctype = (resp.headers.get("content-type") or "").lower()
        assert "event-stream" in ctype, f"expected text/event-stream, got {ctype!r}"

        body = resp.text()
        data_lines = [
            ln
            for ln in body.splitlines()
            if ln.startswith("data:") and "[DONE]" not in ln and "data: [DONE]" not in ln
        ]
        assert len(data_lines) >= 2, f"expected multiple SSE data frames, got {len(data_lines)}"
        assert "[DONE]" in body, "expected SSE stream terminator [DONE]"
    finally:
        page.close()
