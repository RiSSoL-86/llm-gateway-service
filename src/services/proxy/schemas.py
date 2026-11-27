from time import perf_counter
from typing import final

from pydantic import BaseModel, Field

from services.open_router.schemas import OpenRouterAnswer
from services.proxy.enums import Outcome


@final
class ProxyMetrics(BaseModel):
    """Keep timings and tokens of one proxied request, times from `started`."""

    client: str
    # OpenRouter path, the same as ours after `/api/v1/`
    endpoint: str
    model: str | None
    stream: bool
    request_bytes: int
    started: float = Field(default_factory=perf_counter)
    upstream_started: float | None = None
    upstream_headers: float | None = None
    first_byte: float | None = None
    first_token: float | None = None
    upstream_finished: float | None = None
    status: int | None = None
    outcome: Outcome = Outcome.OK
    error: str | None = None
    answer: OpenRouterAnswer = Field(default_factory=OpenRouterAnswer)
