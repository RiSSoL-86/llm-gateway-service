import asyncio
import gc
import logging
from collections.abc import AsyncIterator
from http import HTTPMethod

import httpx

from services.proxy.schemas import ProxyMetrics
from services.proxy.services.proxy import ProxyService
from services.proxy.tests.helpers import metrics_line


async def test_unsent_stream_frees_upstream(upstream, caplog) -> None:
    closed = []

    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield b": OPENROUTER PROCESSING\n\n"

        async def aclose(self) -> None:
            closed.append(True)

    upstream.install(
        handler=lambda _: httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/event-stream"},
            stream=Chunks(),
        )
    )
    caplog.set_level(level=logging.INFO)
    metrics = ProxyMetrics(
        client="tester",
        endpoint="chat/completions",
        model="m",
        stream=True,
        request_bytes=2,
    )

    response = await ProxyService().execute(
        method=HTTPMethod.POST,
        path="chat/completions",
        query="",
        body=b"{}",
        headers={},
        metrics=metrics,
    )
    assert response.status_code == 200
    # Django drops a response it could not send: asyncio closes the stream
    del response
    gc.collect()
    for _ in range(5):
        await asyncio.sleep(delay=0)

    assert closed == [True]
    assert metrics_line(caplog=caplog)["outcome"] == "client_disconnected"
