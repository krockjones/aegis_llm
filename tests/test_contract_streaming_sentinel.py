"""Guardrails on `docs/API_CONTRACT.md` streaming claims (replaces ad-hoc human grep)."""

from __future__ import annotations

from pathlib import Path

import pytest

_DOCS = Path(__file__).resolve().parents[1] / "docs" / "API_CONTRACT.md"


def _streaming_section(md: str) -> str:
    start = md.find("### Streaming (SSE)")
    assert start != -1, "API_CONTRACT.md must contain ### Streaming (SSE)"
    end = md.find("\n### Non-stream", start)
    assert end != -1, "API_CONTRACT.md must contain ### Non-stream after streaming section"
    return md[start:end]


@pytest.mark.scenario("contract-streaming-sentinel")
def test_api_contract_streaming_section_forbids_universal_client_matrix() -> None:
    """Parent plan forbids implying full OpenAI-client SSE matrix coverage."""
    text = _streaming_section(_DOCS.read_text(encoding="utf-8"))
    lowered = text.lower()
    assert "all openai clients" not in lowered
    assert "every openai client" not in lowered
    assert "full sse client matrix" not in lowered
    assert "universal compatibility" not in lowered


@pytest.mark.scenario("contract-streaming-sentinel")
def test_api_contract_streaming_section_has_known_limitations() -> None:
    text = _streaming_section(_DOCS.read_text(encoding="utf-8"))
    assert "#### Known limitations (streaming)" in text
