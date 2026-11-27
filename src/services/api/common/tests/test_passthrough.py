import httpx
import pytest
from django.test import AsyncClient
from django.urls import reverse

from services.api.common.tests.constants import AUTH

OK = {"id": "gen-1", "choices": []}


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        (b"{oops", "application/json"),
        (b'{"model": "m", "messages": "hi", "stream": {"a": 1}}', None),
        (b'{"model": "m"}', "text/plain"),
    ],
)
async def test_sends_any_body_as_is(upstream, body, content_type) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=OK)
    )

    response = await AsyncClient().post(
        path=f"{reverse('api:chat_completions:completions')}?a=1",
        data=body,
        content_type=content_type or "application/json",
        headers=AUTH,
    )

    assert response.status_code == 200
    sent = upstream[0]
    assert sent.content == body
    assert sent.headers["Content-Type"] == (content_type or "application/json")
    assert sent.url.query == b"a=1"


async def test_takes_any_accept(upstream) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=OK)
    )

    response = await AsyncClient().post(
        path=reverse("api:responses:responses"),
        data=b'{"model": "m", "input": "hi", "stream": true}',
        content_type="application/json",
        headers=AUTH | {"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert len(upstream) == 1


async def test_answers_unknown_key_in_json_by_any_accept(upstream) -> None:
    response = await AsyncClient().post(
        path=reverse("api:messages:messages"),
        data=b"{}",
        content_type="application/json",
        headers={"Authorization": "Bearer wrong", "Accept": "text/plain"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": {"message": "Invalid API key"}}
    assert upstream == []


async def test_docs_describe_bodies_and_queries() -> None:
    schema = (await AsyncClient().get(path=reverse("schema-json"))).json()
    paths = schema["paths"]

    chat = paths["/api/v1/chat/completions"]["post"]
    body = chat["requestBody"]["content"]["application/json"]["schema"]
    assert body == {"$ref": "#/components/schemas/ChatCompletionRequest"}
    request = schema["components"]["schemas"]["ChatCompletionRequest"]
    assert "messages" in request["properties"]
    generation = paths["/api/v1/generation"]["get"]
    assert [param["name"] for param in generation["parameters"]] == ["id"]
    endpoints = paths["/api/v1/models/{author}/{slug}/endpoints"]["get"]
    assert {param["name"] for param in endpoints["parameters"]} == {
        "author",
        "slug",
    }
