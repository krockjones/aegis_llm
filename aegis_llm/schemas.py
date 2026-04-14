from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatMessage(BaseModel):
    """Subset of OpenAI chat message (text and simple multimodal parts)."""

    model_config = ConfigDict(extra="ignore")

    role: str = Field(..., min_length=1)
    content: str | list[dict[str, Any]] | None = None


class ChatCompletionRequest(BaseModel):
    """Supported fields for POST /v1/chat/completions (unknown fields ignored)."""

    model_config = ConfigDict(extra="ignore")

    model: str = Field(..., min_length=1)
    messages: list[ChatMessage] = Field(..., min_length=1)
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = Field(None, ge=1)
    stop: str | list[str] | None = None

    def to_backend_payload(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "model": self.model,
            "messages": [m.model_dump(exclude_none=True) for m in self.messages],
            "stream": self.stream,
        }
        if self.temperature is not None:
            d["temperature"] = self.temperature
        if self.top_p is not None:
            d["top_p"] = self.top_p
        if self.max_tokens is not None:
            d["max_tokens"] = self.max_tokens
        if self.stop is not None:
            d["stop"] = self.stop
        return d


class EmbeddingsRequest(BaseModel):
    """Subset of OpenAI POST /v1/embeddings mapped to Ollama POST /api/embed.

    Unknown top-level JSON keys are rejected (Pydantic extra forbid), not ignored.
    """

    model_config = ConfigDict(extra="forbid")

    model: str = Field(..., min_length=1)
    input: str | list[str] = Field(..., description="Text or batch of texts to embed")
    encoding_format: Literal["float"] | None = None
    dimensions: int | None = Field(None, ge=1, description="Passed to Ollama when set")
    truncate: bool | None = Field(
        None,
        description="Ollama: truncate inputs to fit context (default upstream behavior if omitted)",
    )

    @field_validator("input")
    @classmethod
    def input_non_empty_strings(cls, v: str | list[str]) -> str | list[str]:
        if isinstance(v, list):
            if not v:
                raise ValueError("input list must not be empty")
            for i, item in enumerate(v):
                if not isinstance(item, str) or not item.strip():
                    raise ValueError(f"input[{i}] must be a non-empty string")
        elif isinstance(v, str):
            if not v.strip():
                raise ValueError("input must not be empty")
        return v

    def to_ollama_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {"model": self.model, "input": self.input}
        if self.dimensions is not None:
            body["dimensions"] = self.dimensions
        if self.truncate is not None:
            body["truncate"] = self.truncate
        return body
