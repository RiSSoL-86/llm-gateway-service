from typing import Any, final

from pydantic import Field

from apps.common.schemas import PermissiveModel


@final
class MessageRequest(PermissiveModel):
    """Describe the main request fields, the body goes to OpenRouter as is."""

    model: str | None = Field(
        default=None, examples=["anthropic/claude-haiku-4.5"]
    )
    max_tokens: int | None = Field(default=None, examples=[16])
    messages: Any = Field(
        default=None,
        examples=[[{"role": "user", "content": "Say hello in one word"}]],
    )
    stream: bool = Field(
        default=False,
        description="`true`: server-sent events, Anthropic ones.",
    )


@final
class MessageResponse(PermissiveModel):
    """Describe the OpenRouter message, passed through unchanged."""

    id: str
    type: str
    role: str
    model: str
    content: list[dict[str, Any]]
    usage: dict[str, Any] | None = None
