from typing import Any, final

from pydantic import BaseModel, Field

from apps.common.schemas import PermissiveModel


@final
class EmbeddingRequest(PermissiveModel):
    """Describe the main request fields, the body goes to OpenRouter as is."""

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


@final
class EmbeddingModelsQuery(BaseModel):
    """Take the page of the embedding model list."""

    offset: int | None = Field(default=None, examples=[0])
    limit: int | None = Field(default=None, examples=[50])


@final
class EmbeddingModelsResponse(PermissiveModel):
    """Describe the OpenRouter embedding models, passed through unchanged."""

    data: list[dict[str, Any]]
    total_count: int | None = None
    links: dict[str, Any] | None = None
