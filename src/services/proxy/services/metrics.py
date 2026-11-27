import logging
from http import HTTPStatus
from time import perf_counter
from typing import TYPE_CHECKING, Any, final, override

from apps.common.services.base import BaseService
from services.metrics.services.write import WriteMetricService
from services.proxy.constants import METRICS_EVENT
from services.proxy.enums import Outcome

if TYPE_CHECKING:
    from services.proxy.schemas import ProxyMetrics


@final
class ReportProxyMetricsService(BaseService):
    """Report one proxied request: timings, tokens, cost, how it ended."""

    def __init__(self) -> None:
        """Take the service the metric lines are written by."""
        self.write_metric = WriteMetricService()

    @override
    async def execute(self, metrics: ProxyMetrics) -> None:
        """Write the metrics, `overhead_ms` is the time outside OpenRouter."""
        await self.write_metric.execute(
            event=METRICS_EVENT,
            level=self._level(metrics=metrics),
            fields=self._fields(metrics=metrics),
        )

    @classmethod
    def _fields(cls, metrics: ProxyMetrics) -> dict[str, Any]:
        finished = perf_counter()
        upstream_ms = cls._ms(
            start=metrics.upstream_started, end=metrics.upstream_finished
        )
        total_ms = cls._ms(start=metrics.started, end=finished)
        answer = metrics.answer
        usage = answer.usage or {}
        return {
            "client": metrics.client,
            "endpoint": metrics.endpoint,
            "model": metrics.model,
            "upstream_model": answer.model,
            "provider": answer.provider,
            "generation_id": answer.generation_id,
            "stream": metrics.stream,
            "status": metrics.status,
            "outcome": metrics.outcome,
            "error": metrics.error or answer.error,
            "request_bytes": metrics.request_bytes,
            # Chat names first, then `responses` and `messages` (`input_*`)
            "prompt_tokens": cls._first(
                usage.get("prompt_tokens"), usage.get("input_tokens")
            ),
            "completion_tokens": cls._first(
                usage.get("completion_tokens"), usage.get("output_tokens")
            ),
            "total_tokens": usage.get("total_tokens"),
            "cached_tokens": cls._first(
                cls._nested(
                    data=usage,
                    key="prompt_tokens_details",
                    field="cached_tokens",
                ),
                cls._nested(
                    data=usage,
                    key="input_tokens_details",
                    field="cached_tokens",
                ),
                usage.get("cache_read_input_tokens"),
            ),
            "reasoning_tokens": cls._first(
                cls._nested(
                    data=usage,
                    key="completion_tokens_details",
                    field="reasoning_tokens",
                ),
                cls._nested(
                    data=usage,
                    key="output_tokens_details",
                    field="reasoning_tokens",
                ),
            ),
            "cost": usage.get("cost"),
            "upstream_headers_ms": cls._ms(
                start=metrics.started, end=metrics.upstream_headers
            ),
            "ttfb_ms": cls._ms(start=metrics.started, end=metrics.first_byte),
            "ttft_ms": cls._ms(start=metrics.started, end=metrics.first_token),
            "upstream_ms": upstream_ms,
            "total_ms": total_ms,
            "overhead_ms": (
                round(total_ms - upstream_ms, 2)
                if total_ms is not None and upstream_ms is not None
                else None
            ),
        }

    @staticmethod
    def _level(metrics: ProxyMetrics) -> int:
        if metrics.outcome in {
            Outcome.UPSTREAM_UNAVAILABLE,
            Outcome.STREAM_ERROR,
        }:
            return logging.ERROR
        status = metrics.status or HTTPStatus.OK
        if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            return logging.ERROR
        if status >= HTTPStatus.BAD_REQUEST:
            return logging.WARNING
        return logging.INFO

    @staticmethod
    def _ms(start: float | None, end: float | None) -> float | None:
        if start is None or end is None:
            return None
        return round((end - start) * 1000, 2)

    @staticmethod
    def _first(*values: Any) -> Any:
        return next((value for value in values if value is not None), None)

    @staticmethod
    def _nested(data: dict[str, Any], key: str, field: str) -> Any:
        inner = data.get(key)
        return inner.get(field) if isinstance(inner, dict) else None
