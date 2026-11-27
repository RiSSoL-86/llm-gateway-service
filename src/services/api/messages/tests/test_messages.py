import logging
from collections.abc import AsyncIterator

import httpx
from django.test import AsyncClient
from django.urls import reverse

from services.api.common.tests.constants import AUTH
from services.open_router.tests.mock import UPSTREAM_URL
from services.proxy.tests.helpers import metrics_line, read_stream

URL = reverse("api:messages:messages")

SSE_CHUNKS = [
    b"event: message_start\n"
    b'data: {"type":"message_start","message":{"id":"gen-m1",'
    b'"model":"anthropic/claude-haiku-4.5","usage":{"input_tokens":12,'
    b'"cache_read_input_tokens":4,"output_tokens":1}}}\n\n',
    b'data: {"type":"content_block_start","index":0,'
    b'"content_block":{"type":"text","text":""}}\n\n',
    b'data: {"type":"content_block_delta","index":0,'
    b'"delta":{"type":"text_delta","text":"Hi"}}\n\n',
    b'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},'
    b'"usage":{"output_tokens":3,"cost":0.01}}\n\n',
    b'data: {"type":"message_stop"}\n\n',
]


async def test_proxies_anthropic_stream(upstream, caplog) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        for chunk in SSE_CHUNKS:
            yield chunk

    upstream.install(
        handler=lambda _: httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/event-stream"},
            content=chunks(),
        )
    )
    caplog.set_level(level=logging.INFO)
    body = (
        b'{"model": "anthropic/claude-haiku-4.5", "max_tokens": 5,'
        b' "messages": [], "stream": true}'
    )

    response = await AsyncClient().post(
        path=URL,
        data=body,
        content_type="application/json",
        headers=AUTH | {"anthropic-version": "2023-06-01"},
    )

    assert await read_stream(response=response) == b"".join(SSE_CHUNKS)
    sent = upstream[0]
    assert sent.url == f"{UPSTREAM_URL}/messages"
    assert sent.content == body
    assert sent.headers["anthropic-version"] == "2023-06-01"
    fields = metrics_line(caplog=caplog)
    assert fields["endpoint"] == "messages"
    assert fields["stream"] is True
    assert fields["generation_id"] == "gen-m1"
    assert fields["prompt_tokens"] == 12
    assert fields["completion_tokens"] == 3
    assert fields["cached_tokens"] == 4
    assert fields["cost"] == 0.01
    assert fields["ttft_ms"] is not None


async def test_passes_anthropic_error_through(upstream, caplog) -> None:
    error = {
        "type": "error",
        "error": {"type": "invalid_request_error", "message": "bad"},
    }
    upstream.install(
        handler=lambda _: httpx.Response(status_code=400, json=error)
    )

    response = await AsyncClient().post(
        path=URL, data=b"{}", content_type="application/json", headers=AUTH
    )

    assert response.status_code == 400
    assert response.json() == error
    assert metrics_line(caplog=caplog)["error"] == "bad"
