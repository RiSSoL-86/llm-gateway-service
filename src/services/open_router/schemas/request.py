from typing import final

from pydantic import BaseModel


@final
class OpenRouterRequest(BaseModel):
    """Keep the request fields metrics need, the rest is skipped."""

    model: str | None = None
    stream: bool = False
