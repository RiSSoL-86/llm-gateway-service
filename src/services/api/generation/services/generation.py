from collections.abc import Mapping
from http import HTTPMethod
from typing import TYPE_CHECKING, final, override
from urllib.parse import urlencode

from apps.common.services.base import BaseService
from services.open_router.constants import GENERATION_PATH
from services.proxy.schemas import ProxyMetrics
from services.proxy.services.proxy import ProxyService

if TYPE_CHECKING:
    from django.http import HttpResponse, StreamingHttpResponse


@final
class GenerationService(BaseService):
    """Proxy the generation stats request to OpenRouter."""

    def __init__(self) -> None:
        """Take the proxy to OpenRouter."""
        self.proxy = ProxyService()

    @override
    async def execute(
        self,
        client: str,
        generation_id: str,
        headers: Mapping[str, str],
    ) -> HttpResponse | StreamingHttpResponse:
        """Ask OpenRouter for cost and tokens of one generation."""
        metrics = ProxyMetrics(
            client=client,
            endpoint=GENERATION_PATH,
            model=None,
            stream=False,
            request_bytes=0,
        )
        return await self.proxy.execute(
            method=HTTPMethod.GET,
            path=GENERATION_PATH,
            query=urlencode(query={"id": generation_id}),
            body=b"",
            headers=headers,
            metrics=metrics,
        )
