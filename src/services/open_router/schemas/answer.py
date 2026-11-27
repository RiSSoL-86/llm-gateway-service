from typing import Any, final

from pydantic import BaseModel


@final
class OpenRouterAnswer(BaseModel):
    """Keep what was read out of one OpenRouter answer."""

    seen_data: bool = False
    # First text, reasoning or tool call: the real TTFT
    seen_token: bool = False
    generation_id: str | None = None
    model: str | None = None
    provider: str | None = None
    usage: dict[str, Any] | None = None
    error: str | None = None
