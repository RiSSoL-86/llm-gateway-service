from collections.abc import Mapping
from http import HTTPMethod
from typing import TYPE_CHECKING, final, override

from apps.common.services.base import BaseService
from services.open_router.constants import EMBEDDINGS_PATH
from services.open_router.parsers.request import RequestReader
from services.proxy.schemas import ProxyMetrics
from services.proxy.services.proxy import ProxyService

if TYPE_CHECKING:
    from django.http import HttpResponse, StreamingHttpResponse


@final
class EmbeddingService(BaseService):
    """Proxy one embeddings request to OpenRouter."""

    def __init__(self) -> None:
        """Take the proxy to OpenRouter."""
        self.proxy = ProxyService()

    @override
    async def execute(
        self,
        client: str,
        query: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> HttpResponse | StreamingHttpResponse:
        """Send the embeddings request to OpenRouter as is."""
        request = RequestReader.read(body=body)
        metrics = ProxyMetrics(
            client=client,
            endpoint=EMBEDDINGS_PATH,
            model=request.model,
            stream=request.stream,
            request_bytes=len(body),
        )
        return await self.proxy.execute(
            method=HTTPMethod.POST,
            path=EMBEDDINGS_PATH,
            query=query,
            body=body,
            headers=headers,
            metrics=metrics,
        )
