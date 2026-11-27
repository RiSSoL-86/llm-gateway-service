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
        headers: Mapping[str, bytes],
    ) -> httpx.Response:
        """Return the OpenRouter response with its body not read yet."""
        client = OpenRouterClient.get()
        request = client.build_request(
            method=method,
            url=f"{path}?{query}" if query else path,
            content=body or None,
            # Ours go last: a client header never replaces our key
            headers={
                name.encode(): value
                for name, value in {**headers, **self._headers()}.items()
            },
        )
        return await client.send(request=request, stream=True)

    @staticmethod
    def _headers() -> dict[str, bytes]:
        key: str = settings.OPENROUTER_API_KEY  # type: ignore[misc]
        return {
            "Authorization": f"Bearer {key}".encode(),
            # Plain bytes: nothing to decompress, chunks go out as they come
            "Accept-Encoding": b"identity",
        }
