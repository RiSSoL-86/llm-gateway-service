import logging
from collections.abc import Mapping
from typing import Any, final, override

from apps.common.services.base import BaseService
from services.metrics.constants import METRICS_LOGGER

logger = logging.getLogger(name=METRICS_LOGGER)


@final
class WriteMetricService(BaseService):
    """Write one metric line, CloudWatch metric filters read its fields."""

    @override
    async def execute(
        self,
        event: str,
        level: int,
        fields: Mapping[str, Any],
    ) -> None:
        """Log the event with its fields, `event` is the field to filter by."""
        logger.log(
            level=level,
            msg=event,
            extra={"fields": {"event": event, **fields}},
        )
