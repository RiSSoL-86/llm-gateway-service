import asyncio
import gc
import logging
from collections.abc import AsyncIterator
from http import HTTPMethod

import httpx
import pytest

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


async def test_reports_client_gone_before_answer(upstream, caplog) -> None:
    class Hanging(httpx.AsyncByteStream):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            await asyncio.Event().wait()
            yield b""

    upstream.install(
        handler=lambda _: httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            stream=Hanging(),
        )
    )
    caplog.set_level(level=logging.INFO)
    metrics = ProxyMetrics(
        client="tester",
        endpoint="chat/completions",
        model="m",
        stream=False,
        request_bytes=2,
    )
    task = asyncio.create_task(
        coro=ProxyService().execute(
            method=HTTPMethod.POST,
            path="chat/completions",
            query="",
            body=b"{}",
            headers={},
            metrics=metrics,
        )
    )
    for _ in range(5):
        await asyncio.sleep(delay=0)

    # Django cancels the view once the client goes away
    task.cancel()
    with pytest.raises(expected_exception=asyncio.CancelledError):
        await task

    assert metrics_line(caplog=caplog)["outcome"] == "client_disconnected"
