from collections.abc import Mapping
from http import HTTPMethod
from typing import TYPE_CHECKING, final, override

from apps.common.services.base import BaseService
from services.open_router.constants import COMPLETIONS_PATH
from services.proxy.schemas import ProxyMetrics
from services.proxy.services.proxy import ProxyService

if TYPE_CHECKING:
    from django.http import HttpResponse, StreamingHttpResponse


@final
class CompletionService(BaseService):
    """Proxy one text completion to OpenRouter."""

    def __init__(self) -> None:
        """Take the proxy to OpenRouter."""
        self.proxy = ProxyService()

    @override
    async def execute(
        self,
        client: str,
        body: bytes,
        headers: Mapping[str, str],
        model: str | None,
        stream: bool,
    ) -> HttpResponse | StreamingHttpResponse:
        """Send the text completion to OpenRouter as is."""
        metrics = ProxyMetrics(
            client=client,
            endpoint=COMPLETIONS_PATH,
            model=model,
            stream=stream,
            request_bytes=len(body),
        )
        return await self.proxy.execute(
            method=HTTPMethod.POST,
            path=COMPLETIONS_PATH,
            query="",
            body=body,
            headers=headers,
            metrics=metrics,
        )
