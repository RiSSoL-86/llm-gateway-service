from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from services.proxy.constants import METRICS_EVENT

if TYPE_CHECKING:
    import pytest


def metrics_line(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    """Return the fields of the one metrics line of the request."""
    records = [r for r in caplog.records if r.getMessage() == METRICS_EVENT]
    assert len(records) == 1
    return records[0].fields  # type: ignore[attr-defined, no-any-return]


async def read_stream(response: object) -> bytes:
    """Return the whole body of a streaming response."""
    content: AsyncIterator[bytes] = response.streaming_content  # type: ignore[attr-defined]
    return b"".join([chunk async for chunk in content])
