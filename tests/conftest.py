from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aegis_llm.app import create_app
from aegis_llm.config import Settings


@pytest.fixture
def ollama_base() -> str:
    return "http://ollama.test"


@pytest.fixture
def settings(ollama_base: str) -> Settings:
    return Settings(
        backend_type="ollama",
        upstream_base_url=ollama_base,
        listen_host="127.0.0.1",
        listen_port=8765,
        api_keys=(),
        connect_timeout=2.0,
        read_timeout=5.0,
        log_level="INFO",
    )


@pytest.fixture
async def client(settings: Settings):
    app = create_app(settings)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://guard.test") as ac:
            yield ac


@pytest.fixture
async def client_with_keys(settings: Settings, ollama_base: str):
    s = Settings(
        backend_type="ollama",
        upstream_base_url=ollama_base,
        listen_host=settings.listen_host,
        listen_port=settings.listen_port,
        api_keys=("secret-key",),
        connect_timeout=settings.connect_timeout,
        read_timeout=settings.read_timeout,
        log_level="INFO",
    )
    app = create_app(s)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://guard.test") as ac:
            yield ac
