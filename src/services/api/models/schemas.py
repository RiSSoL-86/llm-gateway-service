from typing import Any, final

from pydantic import BaseModel, Field

from apps.common.schemas import PermissiveModel


@final
class ModelsResponse(PermissiveModel):
    """Describe the OpenRouter model list, passed through unchanged."""

    data: list[dict[str, Any]]


@final
class ModelsCountResponse(PermissiveModel):
    """Describe the OpenRouter model count, passed through unchanged."""

    data: dict[str, Any]


@final
class ModelPath(BaseModel):
    """Take the model id from the path: `openai/gpt-4o-mini`."""

    author: str = Field(examples=["openai"])
    slug: str = Field(examples=["gpt-4o-mini"])


@final
class ModelEndpointsResponse(PermissiveModel):
    """Describe the providers of one model, passed through unchanged."""

    data: dict[str, Any]
