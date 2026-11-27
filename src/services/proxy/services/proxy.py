import asyncio
import json
from collections.abc import AsyncIterator, Mapping
from http import HTTPMethod, HTTPStatus
from time import perf_counter
from typing import TYPE_CHECKING, final, override

import httpx
from django.http import HttpResponse, StreamingHttpResponse

from apps.common.services.base import BaseService
from services.open_router.parsers.sniffer import AnswerSniffer
from services.open_router.schemas import ErrorDetail, ErrorResponse
from services.open_router.services.request import OpenRouterRequestService
from services.proxy.constants import (
    ACCOUNT_FIELD,
    EVENT_STREAM,
    FORWARDED_REQUEST_HEADERS,
    FORWARDED_RESPONSE_HEADERS,
    HEADER_ENCODING,
    RATE_LIMIT_HEADER_PREFIX,
    STREAM_HEADERS,
    UPSTREAM_AUTH_FAILED,
    UPSTREAM_STREAM_BROKE,
    UPSTREAM_UNAVAILABLE,
)
from services.proxy.enums import Outcome
from services.proxy.services.metrics import ReportProxyMetricsService

if TYPE_CHECKING:
    from services.proxy.schemas import ProxyMetrics


@final
class ProxyService(BaseService):
    """Proxy one request to OpenRouter, give its answer back as is."""

    def __init__(self) -> None:
        """Take the services the proxy sends and reports through."""
        self.open_router = OpenRouterRequestService()
        self.report_metrics = ReportProxyMetricsService()

    @override
    async def execute(
        self,
        method: HTTPMethod,
        path: str,
        query: str,
        body: bytes,
        headers: Mapping[str, str],
        metrics: ProxyMetrics,
    ) -> HttpResponse | StreamingHttpResponse:
        """Send the request as is, stream the answer back as it comes."""
        sniffer = AnswerSniffer(answer=metrics.answer)
        metrics.upstream_started = perf_counter()
        try:
            upstream = await self.open_router.execute(
                method=method,
                path=path,
                query=query,
                body=body,
                headers=self._forwarded(headers=headers),
            )
        except httpx.HTTPError as exc:
            return await self._unavailable(metrics=metrics, exc=exc)
        except asyncio.CancelledError:
            # Django cancels the view once the client goes away
            await self._disconnected(metrics=metrics)
            raise
        metrics.upstream_headers = perf_counter()
        metrics.status = upstream.status_code

        content_type = upstream.headers.get(key="Content-Type", default="")
        if upstream.is_success and content_type.startswith(EVENT_STREAM):
            stream = self._stream(
                upstream=upstream, metrics=metrics, sniffer=sniffer
            )
            # Started now: an unsent response still frees the upstream on close
            await anext(stream)
            return StreamingHttpResponse(
                streaming_content=stream,
                status=upstream.status_code,
                content_type=content_type,
                headers=STREAM_HEADERS
                | self._backoff(headers=upstream.headers),
            )

        try:
            content = await upstream.aread()
        except httpx.HTTPError as exc:
            return await self._unavailable(metrics=metrics, exc=exc)
        except asyncio.CancelledError:
            await self._disconnected(metrics=metrics)
            raise
        finally:
            await upstream.aclose()
        metrics.upstream_finished = metrics.first_byte = perf_counter()
        # Lists (`/models` is big) carry no usage: only answers and errors
        if method == HTTPMethod.POST or not upstream.is_success:
            sniffer.inspect_json(payload=content)

        if upstream.status_code == HTTPStatus.UNAUTHORIZED:
            # Our OpenRouter key is wrong; 403 (moderation) passes through
            metrics.status = HTTPStatus.BAD_GATEWAY
            metrics.outcome = Outcome.UPSTREAM_ERROR
            metrics.error = f"our key rejected: {metrics.answer.error}"
            await self.report_metrics.execute(metrics=metrics)
            return self._error(
                status=HTTPStatus.BAD_GATEWAY, message=UPSTREAM_AUTH_FAILED
            )

        if not upstream.is_success:
            metrics.outcome = Outcome.UPSTREAM_ERROR
            content = self._without_account(content=content)
        await self.report_metrics.execute(metrics=metrics)
        return HttpResponse(
            content=content,
            status=upstream.status_code,
            content_type=content_type or "application/json",
            headers=self._backoff(headers=upstream.headers),
        )

    async def _stream(
        self,
        upstream: httpx.Response,
        metrics: ProxyMetrics,
        sniffer: AnswerSniffer,
    ) -> AsyncIterator[bytes]:
        try:
            # Priming step, taken by `execute`: nothing goes to the client
            yield b""
            async for chunk in upstream.aiter_bytes():
                if metrics.first_byte is None:
                    metrics.first_byte = perf_counter()
                sniffer.feed(chunk=chunk)
                if metrics.first_token is None and metrics.answer.seen_token:
                    metrics.first_token = perf_counter()
                yield chunk
            sniffer.finish()
            if metrics.answer.error:
                # OpenRouter sends mid-stream errors after the 200 status
                metrics.outcome = Outcome.STREAM_ERROR
        except httpx.HTTPError as exc:
            # The status is already sent: report the error in the stream
            metrics.outcome = Outcome.STREAM_ERROR
            metrics.error = type(exc).__name__
            error = self._error_body(
                status=HTTPStatus.BAD_GATEWAY, message=UPSTREAM_STREAM_BROKE
            )
            yield b"data: " + error + b"\n\n"
        except asyncio.CancelledError, GeneratorExit:
            # The client went away: stop paying for the rest of the answer
            metrics.outcome = Outcome.CLIENT_DISCONNECTED
            raise
        finally:
            metrics.upstream_finished = perf_counter()
            await upstream.aclose()
            await self.report_metrics.execute(metrics=metrics)

    async def _disconnected(self, metrics: ProxyMetrics) -> None:
        # OpenRouter may bill the answer the client never took: still counted
        metrics.upstream_finished = perf_counter()
        metrics.outcome = Outcome.CLIENT_DISCONNECTED
        await self.report_metrics.execute(metrics=metrics)

    async def _unavailable(
        self,
        metrics: ProxyMetrics,
        exc: httpx.HTTPError,
    ) -> HttpResponse:
        status = (
            HTTPStatus.GATEWAY_TIMEOUT
            if isinstance(exc, httpx.TimeoutException)
            else HTTPStatus.BAD_GATEWAY
        )
        metrics.upstream_finished = perf_counter()
        metrics.status = status
        metrics.outcome = Outcome.UPSTREAM_UNAVAILABLE
        metrics.error = type(exc).__name__
        await self.report_metrics.execute(metrics=metrics)
        return self._error(status=status, message=UPSTREAM_UNAVAILABLE)

    @classmethod
    def _error(cls, status: HTTPStatus, message: str) -> HttpResponse:
        return HttpResponse(
            content=cls._error_body(status=status, message=message),
            status=status,
            content_type="application/json",
        )

    @staticmethod
    def _error_body(status: HTTPStatus, message: str) -> bytes:
        error = ErrorResponse(
            error=ErrorDetail(code=status.value, message=message)
        )
        return error.model_dump_json().encode()

    @staticmethod
    def _forwarded(headers: Mapping[str, str]) -> dict[str, bytes]:
        # Case-insensitive get; latin-1 back to the very bytes the client sent
        return {
            name: value.encode(encoding=HEADER_ENCODING)
            for name in FORWARDED_REQUEST_HEADERS
            if (value := headers.get(name))
        }

    @staticmethod
    def _backoff(headers: httpx.Headers) -> dict[str, str]:
        return {
            name: value
            for name, value in headers.items()
            if name in FORWARDED_RESPONSE_HEADERS
            or name.startswith(RATE_LIMIT_HEADER_PREFIX)
        }

    @staticmethod
    def _without_account(content: bytes) -> bytes:
        if f'"{ACCOUNT_FIELD}"'.encode() not in content:
            return content
        try:
            data = json.loads(s=content)
        except ValueError:
            return content
        if not isinstance(data, dict):
            return content
        data.pop(ACCOUNT_FIELD, None)
        return json.dumps(obj=data).encode()
