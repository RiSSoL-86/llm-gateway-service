import logging
from collections.abc import AsyncIterator

import httpx
import pytest
from django.test import AsyncClient
from django.urls import reverse

from services.api.common.tests.constants import AUTH
from services.open_router.tests.mock import UPSTREAM_URL
from services.proxy.tests.helpers import metrics_line, read_stream

URL = reverse("api:chat_completions:completions")

COMPLETION = {
    "id": "gen-1",
    "object": "chat.completion",
    "created": 1,
    "model": "openai/gpt-4o-mini",
    "provider": "OpenAI",
    "choices": [{"message": {"role": "assistant", "content": "Hi"}}],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 2,
        "total_tokens": 12,
        "cost": 0.0001,
        "prompt_tokens_details": {"cached_tokens": 4},
    },
}
SSE_CHUNKS = [
    b": OPENROUTER PROCESSING\n\n",
    b'data: {"id":"gen-2","model":"m","provider":"P",'
    b'"choices":[{"delta":{"content":"He"}}]}\n\ndata: {"id":"gen-2",',
    b'"choices":[{"delta":{"content":"llo"}}]}\n\n',
    b'data: {"id":"gen-2","choices":[],"usage":{"prompt_tokens":5,'
    b'"completion_tokens":2,"total_tokens":7}}\n\n',
    b"data: [DONE]\n\n",
]


async def test_rejects_unknown_key(upstream) -> None:
    response = await AsyncClient().post(
        path=URL,
        data={"model": "m", "messages": []},
        content_type="application/json",
        headers={"Authorization": "Bearer wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": {"message": "Invalid API key"}}
    assert upstream == []


async def test_proxies_json_answer_unchanged(upstream, caplog) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=COMPLETION)
    )
    body = b'{"model": "openai/gpt-4o-mini",  "messages": [], "x": 1}'
    caplog.set_level(level=logging.INFO)

    response = await AsyncClient().post(
        path=URL,
        data=body,
        content_type="application/json",
        headers=AUTH | {"X-Title": "my-app", "Cookie": "a=b"},
    )

    assert response.status_code == 200
    assert response.json() == COMPLETION
    sent = upstream[0]
    assert sent.url == f"{UPSTREAM_URL}/chat/completions"
    assert sent.content == body
    assert sent.headers["Authorization"] == "Bearer sk-or-real-key"
    assert sent.headers["X-Title"] == "my-app"
    assert "Cookie" not in sent.headers
    fields = metrics_line(caplog=caplog)
    assert fields["client"] == "tester"
    assert fields["endpoint"] == "chat/completions"
    assert fields["model"] == "openai/gpt-4o-mini"
    assert fields["prompt_tokens"] == 10
    assert fields["cached_tokens"] == 4
    assert fields["cost"] == 0.0001
    assert fields["generation_id"] == "gen-1"
    assert fields["outcome"] == "ok"
    assert isinstance(fields["overhead_ms"], float)


async def test_proxies_stream_chunk_by_chunk(upstream, caplog) -> None:
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
        data={"model": "m", "messages": [], "stream": True},
        content_type="application/json",
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/event-stream"
    assert await read_stream(response=response) == b"".join(SSE_CHUNKS)
    fields = metrics_line(caplog=caplog)
    assert fields["stream"] is True
    assert fields["completion_tokens"] == 2
    assert fields["provider"] == "P"
    assert fields["ttft_ms"] is not None
    assert fields["ttfb_ms"] <= fields["ttft_ms"]


@pytest.mark.parametrize(
    ("status", "message"),
    [(402, "Insufficient credits"), (403, "Input was flagged")],
)
async def test_passes_upstream_errors_through(
    upstream, status: int, message: str
) -> None:
    error = {"error": {"code": status, "message": message}}
    upstream.install(
        handler=lambda _: httpx.Response(status_code=status, json=error)
    )

    response = await AsyncClient().post(
        path=URL,
        data={"model": "m", "messages": []},
        content_type="application/json",
        headers=AUTH,
    )

    assert response.status_code == status
    assert response.json() == error


async def test_passes_backoff_headers_through(upstream) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(
            status_code=429,
            headers={
                "Retry-After": "7",
                "X-RateLimit-Remaining": "0",
                "Set-Cookie": "ours=1",
            },
            json={"error": {"code": 429, "message": "Rate limited"}},
        )
    )

    response = await AsyncClient().post(
        path=URL,
        data={"model": "m", "messages": []},
        content_type="application/json",
        headers=AUTH,
    )

    assert response.status_code == 429
    assert response["Retry-After"] == "7"
    assert response["X-RateLimit-Remaining"] == "0"
    assert "Set-Cookie" not in response.headers


async def test_hides_our_account_in_errors(upstream) -> None:
    error = {"error": {"code": 400, "message": "bad model"}}
    upstream.install(
        handler=lambda _: httpx.Response(
            status_code=400, json={**error, "user_id": "user_1"}
        )
    )

    response = await AsyncClient().post(
        path=URL,
        data={"model": "m", "messages": []},
        content_type="application/json",
        headers=AUTH,
    )

    assert response.status_code == 400
    assert response.json() == error


async def test_hides_our_rejected_key(upstream) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=401, json={"error": {}})
    )

    response = await AsyncClient().post(
        path=URL,
        data={"model": "m", "messages": []},
        content_type="application/json",
        headers=AUTH,
    )

    assert response.status_code == 502


async def test_upstream_down(upstream, caplog) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(message="down", request=request)

    upstream.install(handler=fail)

    response = await AsyncClient().post(
        path=URL,
        data={"model": "m", "messages": []},
        content_type="application/json",
        headers=AUTH,
    )

    assert response.status_code == 502
    assert response.json()["error"]["message"] == "Upstream is unavailable"
    assert metrics_line(caplog=caplog)["outcome"] == "upstream_unavailable"
