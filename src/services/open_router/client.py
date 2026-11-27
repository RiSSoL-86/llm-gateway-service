from typing import ClassVar, final

import httpx
from django.conf import settings

from services.open_router.constants import KEEPALIVE_EXPIRY


@final
class OpenRouterClient:
    """Hold the one HTTP client to OpenRouter the whole worker shares."""

    _client: ClassVar[httpx.AsyncClient | None] = None

    @classmethod
    def get(cls) -> httpx.AsyncClient:
        """Return the shared client, built on the first call."""
        if cls._client is None:
            cls._client = cls._build()
        return cls._client

    @staticmethod
    def _build() -> httpx.AsyncClient:
        # The real key is added per request, not here
        return httpx.AsyncClient(
            base_url=settings.OPENROUTER_BASE_URL,  # type: ignore[misc]
            timeout=httpx.Timeout(
                connect=settings.UPSTREAM_CONNECT_TIMEOUT,  # type: ignore[misc]
                read=settings.UPSTREAM_READ_TIMEOUT,  # type: ignore[misc]
                write=settings.UPSTREAM_CONNECT_TIMEOUT,  # type: ignore[misc]
                pool=settings.UPSTREAM_CONNECT_TIMEOUT,  # type: ignore[misc]
            ),
            limits=httpx.Limits(
                max_connections=settings.UPSTREAM_MAX_CONNECTIONS,  # type: ignore[misc]
                max_keepalive_connections=settings.UPSTREAM_MAX_CONNECTIONS,  # type: ignore[misc]
                keepalive_expiry=KEEPALIVE_EXPIRY,
            ),
        )
