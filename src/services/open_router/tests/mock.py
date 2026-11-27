from collections.abc import Callable
from typing import TYPE_CHECKING

import httpx

from services.open_router.client import OpenRouterClient

if TYPE_CHECKING:
    import pytest

UPSTREAM_URL = "https://upstream.test/api/v1"

Handler = Callable[[httpx.Request], httpx.Response]


class MockOpenRouter(list[httpx.Request]):
    """OpenRouter mock: keeps the requests it got."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Take the monkeypatch the shared client is swapped by."""
        super().__init__()
        self._monkeypatch = monkeypatch

    def install(self, handler: Handler) -> None:
        """Answer every OpenRouter request with the handler."""

        def record(request: httpx.Request) -> httpx.Response:
            self.append(request)
            return handler(request)

        client = httpx.AsyncClient(
            base_url=UPSTREAM_URL,
            transport=httpx.MockTransport(handler=record),
        )
        self._monkeypatch.setattr(
            target=OpenRouterClient, name="_client", value=client
        )
