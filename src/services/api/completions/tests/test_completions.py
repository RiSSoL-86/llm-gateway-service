import logging
from collections.abc import AsyncIterator

import httpx
from django.test import AsyncClient
from django.urls import reverse

from services.api.common.tests.constants import AUTH
from services.open_router.tests.mock import UPSTREAM_URL
from services.proxy.tests.helpers import metrics_line, read_stream

URL = reverse("api:completions:completions")

SSE_CHUNKS = [
    b'data: {"id":"gen-3","choices":[{"text":"He"}]}\n\n',
    b'data: {"id":"gen-3","choices":[{"text":"llo"}],'
    b'"usage":{"prompt_tokens":3,"completion_tokens":2}}\n\n',
    b"data: [DONE]\n\n",
]


async def test_proxies_text_stream(upstream, caplog) -> None:
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
    body = b'{"model": "m", "prompt": "Hi", "stream": true}'

    response = await AsyncClient().post(
        path=URL, data=body, content_type="application/json", headers=AUTH
    )

    assert response.status_code == 200
    assert await read_stream(response=response) == b"".join(SSE_CHUNKS)
    assert upstream[0].url == f"{UPSTREAM_URL}/completions"
    assert upstream[0].content == body
    fields = metrics_line(caplog=caplog)
    assert fields["endpoint"] == "completions"
    assert fields["completion_tokens"] == 2
    assert fields["ttft_ms"] is not None


async def test_proxies_token_prompt(upstream) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(
            status_code=200, json={"id": "gen-4", "choices": []}
        )
    )
    body = b'{"model": "m", "prompt": [[1212, 318], [42]]}'

    response = await AsyncClient().post(
        path=URL, data=body, content_type="application/json", headers=AUTH
    )

    assert response.status_code == 200
    assert upstream[0].content == body
