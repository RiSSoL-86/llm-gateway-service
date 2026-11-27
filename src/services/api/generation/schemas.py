from typing import Any, final

from pydantic import BaseModel, Field

from apps.common.schemas import PermissiveModel


@final
class GenerationQuery(BaseModel):
    """Take the generation id: the `id` of a completion answer."""

    id: str | None = Field(
        default=None,
        description="Required by OpenRouter.",
        examples=["gen-1234567890-abcdef"],
    )


@final
class GenerationResponse(PermissiveModel):
    """Describe the OpenRouter generation stats, passed through unchanged."""

    data: dict[str, Any]
