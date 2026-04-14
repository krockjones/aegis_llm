from __future__ import annotations

import json
from typing import Any

import httpx
from starlette.responses import JSONResponse

from aegis_llm.logging_setup import get_logger

_log = get_logger("errors")

_BODY_PREVIEW_MAX = 512


def error_payload(
    message: str,
    type_: str,
    *,
    code: str | None = None,
    param: str | None = None,
) -> dict[str, Any]:
    """Canonical OpenAI-style error object (subset)."""
    err: dict[str, Any] = {"message": message, "type": type_}
    if code is not None:
        err["code"] = code
    if param is not None:
        err["param"] = param
    return {"error": err}


def json_error_response(status_code: int, message: str, type_: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_payload(message, type_))


def upstream_json_response(exc: BaseException) -> JSONResponse:
    if isinstance(exc, httpx.TimeoutException):
        return json_error_response(504, "Upstream timeout", "timeout")
    if isinstance(exc, httpx.ConnectError):
        return json_error_response(502, "Upstream connection failed", "connection_error")
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        text = exc.response.text or ""
        preview = text[:_BODY_PREVIEW_MAX]
        _log.warning(
            "Upstream HTTP error: status=%s body_preview=%r",
            status,
            preview,
        )
        return json_error_response(
            502,
            f"Upstream returned HTTP {status}",
            "upstream_http_error",
        )
    return json_error_response(502, str(exc), "upstream_error")


def sse_error_termination(message: str, type_: str) -> bytes:
    """One SSE error event followed by [DONE] (clients often expect stream termination)."""
    payload = json.dumps(error_payload(message, type_))
    return f"data: {payload}\n\ndata: [DONE]\n\n".encode()
