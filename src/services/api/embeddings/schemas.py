from typing import Any, final

from pydantic import Field

from apps.common.schemas import PermissiveModel


@final
class EmbeddingRequest(PermissiveModel):
    """List the request fields the gateway reads, any other is let through."""

    model: str | None = Field(
        default=None, examples=["openai/text-embedding-3-small"]
    )
    input: Any = Field(
        default=None,
        description="Text, a list of texts or of token lists.",
        examples=["The quick brown fox"],
    )


@final
class EmbeddingResponse(PermissiveModel):
    """Describe the OpenRouter embeddings, passed through unchanged."""

    object: str
    data: list[dict[str, Any]]
    model: str
    usage: dict[str, Any] | None = None
