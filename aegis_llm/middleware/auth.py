from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from aegis_llm.errors import error_payload


def _public_path(path: str) -> bool:
    return path in ("/healthz", "/readyz") or path == "/" or path.startswith("/docs") or path in (
        "/openapi.json",
        "/redoc",
    )


class OptionalApiKeyMiddleware(BaseHTTPMiddleware):
    """Require Bearer token when api_keys is non-empty; exempt health and docs."""

    def __init__(self, app, api_keys: tuple[str, ...]) -> None:
        super().__init__(app)
        self._keys = frozenset(api_keys)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._keys or _public_path(request.url.path):
            return await call_next(request)

        auth = request.headers.get("authorization") or ""
        parts = auth.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                error_payload("Missing or invalid Authorization header", "authentication_error"),
                status_code=401,
            )
        token = parts[1].strip()
        if token not in self._keys:
            return JSONResponse(
                error_payload("Invalid API key", "authentication_error"),
                status_code=403,
            )
        return await call_next(request)
