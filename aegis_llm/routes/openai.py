from __future__ import annotations

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from aegis_llm.errors import sse_error_termination, upstream_json_response
from aegis_llm.schemas import ChatCompletionRequest, EmbeddingsRequest

router = APIRouter(tags=["openai"])

_UPSTREAM_INVALID_JSON = "Upstream returned invalid JSON"


@router.get("/v1/models")
async def list_models(request: Request) -> JSONResponse:
    backend = request.app.state.backend
    settings = request.app.state.settings
    try:
        models = await backend.list_models()
    except httpx.TimeoutException as e:
        return upstream_json_response(e)
    except httpx.ConnectError as e:
        return upstream_json_response(e)
    except httpx.HTTPStatusError as e:
        return upstream_json_response(e)
    except OSError as e:
        return upstream_json_response(e)
    except ValueError as e:
        return upstream_json_response(e)
    payload = {"object": "list", "data": models}
    return JSONResponse(
        content=payload,
        headers={
            "X-AegisLLM-Backend": backend.name,
            "X-AegisLLM-Upstream-Base": settings.upstream_base_url,
        },
    )


@router.post("/v1/embeddings", response_model=None)
async def create_embeddings(request: Request, body: EmbeddingsRequest) -> JSONResponse:
    backend = request.app.state.backend
    try:
        result = await backend.embeddings(body.to_ollama_body())
    except httpx.TimeoutException as e:
        return upstream_json_response(e)
    except httpx.ConnectError as e:
        return upstream_json_response(e)
    except httpx.HTTPStatusError as e:
        return upstream_json_response(e)
    except OSError as e:
        return upstream_json_response(e)
    except ValueError as e:
        return upstream_json_response(e)

    return JSONResponse(
        content=result,
        headers={"X-AegisLLM-Backend": backend.name},
    )


@router.post("/v1/chat/completions", response_model=None)
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
) -> JSONResponse | StreamingResponse:
    backend = request.app.state.backend
    payload = body.to_backend_payload()
    stream = body.stream
    if stream:

        async def gen():
            try:
                async for chunk in backend.chat_completion_stream(payload):
                    yield chunk
            except httpx.TimeoutException:
                yield sse_error_termination("Upstream timeout", "timeout")
            except httpx.ConnectError:
                yield sse_error_termination("Upstream connection failed", "connection_error")
            except httpx.HTTPStatusError as e:
                yield sse_error_termination(
                    f"Upstream HTTP {e.response.status_code}",
                    "upstream_http_error",
                )
            except OSError as e:
                yield sse_error_termination(str(e), "upstream_error")
            except ValueError as e:
                if str(e) == _UPSTREAM_INVALID_JSON:
                    yield sse_error_termination(_UPSTREAM_INVALID_JSON, "upstream_error")
                else:
                    yield sse_error_termination(str(e), "invalid_request_error")

        return StreamingResponse(gen(), media_type="text/event-stream")

    try:
        result = await backend.chat_completion(payload)
    except ValueError as e:
        if str(e) == _UPSTREAM_INVALID_JSON:
            return upstream_json_response(e)
        return JSONResponse(
            status_code=400,
            content={"error": {"message": str(e), "type": "invalid_request_error"}},
        )
    except httpx.TimeoutException as e:
        return upstream_json_response(e)
    except httpx.ConnectError as e:
        return upstream_json_response(e)
    except httpx.HTTPStatusError as e:
        return upstream_json_response(e)
    except OSError as e:
        return upstream_json_response(e)

    return JSONResponse(
        content=result,
        headers={
            "X-AegisLLM-Backend": backend.name,
        },
    )
