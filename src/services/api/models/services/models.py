from collections.abc import Mapping
from http import HTTPMethod
from typing import TYPE_CHECKING, final, override

from apps.common.services.base import BaseService
from services.open_router.constants import MODELS_PATH
from services.proxy.schemas import ProxyMetrics
from services.proxy.services.proxy import ProxyService

if TYPE_CHECKING:
    from django.http import HttpResponse, StreamingHttpResponse


@final
class ModelsService(BaseService):
    """Proxy the model list request to OpenRouter."""

    def __init__(self) -> None:
        """Take the proxy to OpenRouter."""
        self.proxy = ProxyService()

    @override
    async def execute(
        self,
        client: str,
        query: str,
        headers: Mapping[str, str],
    ) -> HttpResponse | StreamingHttpResponse:
        """Ask OpenRouter for its models with the client's filters."""
        metrics = ProxyMetrics(
            client=client,
            endpoint=MODELS_PATH,
            model=None,
            stream=False,
            request_bytes=0,
        )
        return await self.proxy.execute(
            method=HTTPMethod.GET,
            path=MODELS_PATH,
            query=query,
            body=b"",
            headers=headers,
            metrics=metrics,
        )
