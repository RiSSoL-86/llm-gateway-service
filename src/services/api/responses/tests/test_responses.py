import logging
from collections.abc import AsyncIterator

import httpx
from django.test import AsyncClient
from django.urls import reverse

from services.api.common.tests.constants import AUTH
from services.open_router.tests.mock import UPSTREAM_URL
from services.proxy.tests.helpers import metrics_line, read_stream

URL = reverse("api:responses:responses")

RESPONSE = {
    "id": "gen-r1",
    "object": "response",
    "model": "openai/gpt-4o-mini",
    "output": [{"type": "message", "content": [{"text": "Hi"}]}],
    "usage": {
        "input_tokens": 9,
        "output_tokens": 2,
        "total_tokens": 11,
        "cost": 0.0002,
        "input_tokens_details": {"cached_tokens": 3},
        "output_tokens_details": {"reasoning_tokens": 1},
    },
}
SSE_CHUNKS = [
    b"event: response.created\n"
    b'data: {"type":"response.created","response":{"id":"gen-r2",'
    b'"model":"m","usage":null}}\n\n',
    b'data: {"type":"response.output_text.delta","delta":""}\n\n',
    b'data: {"type":"response.output_text.delta","delta":"Hi"}\n\n',
    b'data: {"type":"response.completed","response":{"id":"gen-r2",'
    b'"usage":{"input_tokens":5,"output_tokens":1,"cost":0.1}}}\n\n',
]


async def test_proxies_json_answer_with_usage(upstream, caplog) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=RESPONSE)
    )
    caplog.set_level(level=logging.INFO)
    body = b'{"model": "openai/gpt-4o-mini", "input": "hi", "x": 1}'

    response = await AsyncClient().post(
        path=URL, data=body, content_type="application/json", headers=AUTH
    )

    assert response.status_code == 200
    assert response.json() == RESPONSE
    assert upstream[0].url == f"{UPSTREAM_URL}/responses"
    assert upstream[0].content == body
    fields = metrics_line(caplog=caplog)
    assert fields["endpoint"] == "responses"
    assert fields["model"] == "openai/gpt-4o-mini"
    assert fields["generation_id"] == "gen-r1"
    assert fields["prompt_tokens"] == 9
    assert fields["completion_tokens"] == 2
    assert fields["cached_tokens"] == 3
    assert fields["reasoning_tokens"] == 1
    assert fields["cost"] == 0.0002


async def test_proxies_event_stream(upstream, caplog) -> None:
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

    response = await AsyncClient().post(
        path=URL,
        data={"model": "m", "input": "hi", "stream": True},
        content_type="application/json",
        headers=AUTH,
    )

    assert await read_stream(response=response) == b"".join(SSE_CHUNKS)
    fields = metrics_line(caplog=caplog)
    assert fields["stream"] is True
    assert fields["generation_id"] == "gen-r2"
    assert fields["upstream_model"] == "m"
    assert fields["prompt_tokens"] == 5
    assert fields["cost"] == 0.1
    assert fields["ttft_ms"] is not None
    assert fields["outcome"] == "ok"
