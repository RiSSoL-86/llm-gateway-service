from typing import Any, final

from pydantic import Field

from apps.common.schemas import PermissiveModel


@final
class ResponseRequest(PermissiveModel):
    """Describe the main request fields, the body goes to OpenRouter as is."""

    model: str | None = Field(default=None, examples=["openai/gpt-4o-mini"])
    input: Any = Field(
        default=None,
        description="Text or a list of input items.",
        examples=["Say hello in one word"],
    )
    stream: bool = Field(
        default=False,
        description="`true`: server-sent events, `response.*` by event.",
    )


@final
class ResponseResponse(PermissiveModel):
    """Describe the OpenRouter response, passed through unchanged."""

    id: str
    object: str
    model: str
    output: list[dict[str, Any]]
    usage: dict[str, Any] | None = None
