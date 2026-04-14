from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from aegis_llm.backends.factory import create_backend
from aegis_llm.config import Settings, load_settings
from aegis_llm.errors import error_payload
from aegis_llm.logging_setup import setup_logging
from aegis_llm.middleware.access_log import AccessLogMiddleware
from aegis_llm.middleware.auth import OptionalApiKeyMiddleware
from aegis_llm.middleware.request_id import RequestIdMiddleware
from aegis_llm.routes import health, openai
from aegis_llm.version import __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or load_settings()
    setup_logging(s.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        timeout = s.upstream_timeout()
        client = httpx.AsyncClient(timeout=timeout, limits=httpx.Limits(max_keepalive_connections=32))
        app.state.http_client = client
        app.state.backend = create_backend(s, client)
        yield
        await client.aclose()

    app = FastAPI(
        title="AegisLLM Guard",
        version=__version__,
        lifespan=lifespan,
        summary=(
            f"OpenAI-compatible reliability gateway for Ollama (v{__version__}). "
            "Not a universal LLM platform or full OpenAI API mirror—see docs."
        ),
    )
    app.state.settings = s

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        parts: list[str] = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", ()) if x != "body")
            parts.append(f"{loc}: {err.get('msg', 'invalid')}")
        message = "; ".join(parts) if parts else "Invalid request body"
        return JSONResponse(
            status_code=400,
            content=error_payload(message, "invalid_request_error"),
        )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(OptionalApiKeyMiddleware, api_keys=s.api_keys)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(openai.router)

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "service": "aegis-llm",
            "product": "AegisLLM Guard",
            "version": __version__,
            "positioning": "OpenAI-compatible reliability gateway for Ollama (first backend).",
        }

    return app
