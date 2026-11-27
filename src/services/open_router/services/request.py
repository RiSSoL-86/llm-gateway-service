from collections.abc import Mapping
from http import HTTPMethod
from typing import TYPE_CHECKING, final, override

from django.conf import settings

from apps.common.services.base import BaseService
from services.open_router.client import OpenRouterClient

if TYPE_CHECKING:
    import httpx


@final
class OpenRouterRequestService(BaseService):
    """Send one request to an OpenRouter path with our real key."""

    @override
    async def execute(
        self,
        method: HTTPMethod,
        path: str,
        query: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> httpx.Response:
        """Return the OpenRouter response with its body not read yet."""
        client = OpenRouterClient.get()
        request = client.build_request(
            method=method,
            url=f"{path}?{query}" if query else path,
            content=body or None,
            # Ours go last: a client header never replaces our key
            headers={**headers, **self._headers(has_body=bool(body))},
        )
        return await client.send(request=request, stream=True)

    @staticmethod
    def _headers(has_body: bool) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",  # type: ignore[misc]
            # Plain bytes: nothing to decompress, chunks go out as they come
            "Accept-Encoding": "identity",
        }
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers
