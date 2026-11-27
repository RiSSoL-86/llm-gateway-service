from typing import Any, final

from pydantic import Field

from apps.common.schemas import PermissiveModel


@final
class ChatCompletionRequest(PermissiveModel):
    """Describe the main request fields, the body goes to OpenRouter as is."""

    model: str | None = Field(default=None, examples=["openai/gpt-4o-mini"])
    messages: list[dict[str, Any]] = Field(
        default_factory=list,
        examples=[[{"role": "user", "content": "Say hello in one word"}]],
    )
    stream: bool = Field(
        default=False,
        description="`true`: server-sent events, chunk by chunk.",
    )


@final
class ChatCompletionResponse(PermissiveModel):
    """Describe the OpenRouter answer, passed through unchanged."""

    id: str
    object: str
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, Any] | None = None
