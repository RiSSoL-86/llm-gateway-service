import logging

from services.metrics.constants import METRICS_LOGGER
from services.metrics.services.write import WriteMetricService


async def test_writes_event_with_fields(caplog) -> None:
    caplog.set_level(level=logging.INFO, logger=METRICS_LOGGER)

    await WriteMetricService().execute(
        event="sample", level=logging.WARNING, fields={"total_ms": 1.5}
    )

    [record] = caplog.records
    assert record.levelno == logging.WARNING
    assert record.getMessage() == "sample"
    assert record.fields == {"event": "sample", "total_ms": 1.5}
