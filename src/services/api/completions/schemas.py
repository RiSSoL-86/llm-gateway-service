from typing import Any, final

from pydantic import Field

from apps.common.schemas import PermissiveModel


@final
class CompletionRequest(PermissiveModel):
    """List the request fields the gateway reads, any other is let through."""

    model: str | None = Field(default=None, examples=["openai/gpt-4o-mini"])
    prompt: str | list[str] = Field(default="", examples=["Say hello"])
    stream: bool = Field(
        default=False,
        description="`true`: server-sent events, chunk by chunk.",
    )


@final
class CompletionResponse(PermissiveModel):
    """Describe the OpenRouter text completion, passed through unchanged."""

    id: str
    object: str
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, Any] | None = None
