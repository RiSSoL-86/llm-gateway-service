import logging

import httpx
from django.test import AsyncClient
from django.urls import reverse

from services.api.common.tests.constants import AUTH
from services.open_router.tests.mock import UPSTREAM_URL
from services.proxy.tests.helpers import metrics_line

URL = reverse("api:models:models")

MODELS = {"data": [{"id": "openai/gpt-4o-mini", "context_length": 128000}]}


async def test_proxies_model_list_with_query(upstream, caplog) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=MODELS)
    )
    caplog.set_level(level=logging.INFO)

    response = await AsyncClient().get(
        path=f"{URL}?category=programming", headers=AUTH | {"Cookie": "a=b"}
    )

    assert response.status_code == 200
    assert response.json() == MODELS
    sent = upstream[0]
    assert sent.method == "GET"
    assert sent.url == f"{UPSTREAM_URL}/models?category=programming"
    assert sent.content == b""
    assert sent.headers["Authorization"] == "Bearer sk-or-real-key"
    assert "Content-Type" not in sent.headers
    assert "Cookie" not in sent.headers
    fields = metrics_line(caplog=caplog)
    assert fields["endpoint"] == "models"
    assert fields["status"] == 200


async def test_rejects_unknown_key(upstream) -> None:
    response = await AsyncClient().get(
        path=URL, headers={"Authorization": "Bearer wrong"}
    )

    assert response.status_code == 401
    assert upstream == []


async def test_proxies_model_count(upstream) -> None:
    count = {"data": {"count": 300}}
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=count)
    )

    response = await AsyncClient().get(
        path=f"{reverse('api:models:count')}?output_modalities=text",
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json() == count
    assert upstream[0].url == (
        f"{UPSTREAM_URL}/models/count?output_modalities=text"
    )


async def test_proxies_model_endpoints(upstream, caplog) -> None:
    endpoints = {"data": {"id": "openai/gpt-4o-mini", "endpoints": []}}
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=endpoints)
    )
    caplog.set_level(level=logging.INFO)
    url = reverse(
        "api:models:endpoints",
        kwargs={"author": "openai", "slug": "gpt-4o-mini:free"},
    )

    response = await AsyncClient().get(path=url, headers=AUTH)

    assert response.status_code == 200
    assert response.json() == endpoints
    assert upstream[0].url == (
        f"{UPSTREAM_URL}/models/openai/gpt-4o-mini:free/endpoints"
    )
    fields = metrics_line(caplog=caplog)
    assert fields["endpoint"] == "models/{author}/{slug}/endpoints"
    assert fields["model"] == "openai/gpt-4o-mini:free"


async def test_encodes_model_path_again(upstream) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=404, json={})
    )

    response = await AsyncClient().get(
        path="/api/v1/models/a%3Fb/c%23d/endpoints", headers=AUTH
    )

    assert response.status_code == 404
    assert upstream[0].url.raw_path == b"/api/v1/models/a%3Fb/c%23d/endpoints"
