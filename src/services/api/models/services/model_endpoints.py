from collections.abc import Mapping
from http import HTTPMethod
from typing import TYPE_CHECKING, final, override
from urllib.parse import quote

from apps.common.services.base import BaseService
from services.open_router.constants import MODEL_ENDPOINTS_PATH
from services.proxy.schemas import ProxyMetrics
from services.proxy.services.proxy import ProxyService

if TYPE_CHECKING:
    from django.http import HttpResponse, StreamingHttpResponse


@final
class ModelEndpointsService(BaseService):
    """Proxy the request for the providers of one model to OpenRouter."""

    def __init__(self) -> None:
        """Take the proxy to OpenRouter."""
        self.proxy = ProxyService()

    @override
    async def execute(
        self,
        client: str,
        author: str,
        slug: str,
        query: str,
        headers: Mapping[str, str],
    ) -> HttpResponse | StreamingHttpResponse:
        """Ask OpenRouter which providers serve the model, at what price."""
        model = f"{author}/{slug}"
        metrics = ProxyMetrics(
            client=client,
            # The path template: one metric for all models
            endpoint=MODEL_ENDPOINTS_PATH,
            model=model,
            stream=False,
            request_bytes=0,
        )
        return await self.proxy.execute(
            method=HTTPMethod.GET,
            # Encoded again as the client sent it: Django decoded the path
            path=MODEL_ENDPOINTS_PATH.format(
                author=quote(string=author, safe=":"),
                slug=quote(string=slug, safe=":"),
            ),
            query=query,
            body=b"",
            headers=headers,
            metrics=metrics,
        )
