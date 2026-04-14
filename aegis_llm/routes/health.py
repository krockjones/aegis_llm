from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> JSONResponse:
    backend = request.app.state.backend
    ok, err = await backend.health_probe()
    if ok:
        return JSONResponse({"status": "ready", "backend": backend.name})
    return JSONResponse(
        {"status": "not_ready", "backend": backend.name, "detail": err},
        status_code=503,
    )
