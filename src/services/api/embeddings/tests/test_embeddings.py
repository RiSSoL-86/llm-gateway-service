import logging

import httpx
from django.test import AsyncClient
from django.urls import reverse

from services.api.common.tests.constants import AUTH
from services.open_router.tests.mock import UPSTREAM_URL
from services.proxy.tests.helpers import metrics_line

URL = reverse("api:embeddings:embeddings")

EMBEDDINGS = {
    "object": "list",
    "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
    "model": "openai/text-embedding-3-small",
    "usage": {"prompt_tokens": 4, "total_tokens": 4, "cost": 0.00000008},
}


async def test_proxies_embeddings_unchanged(upstream, caplog) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=EMBEDDINGS)
    )
    caplog.set_level(level=logging.INFO)
    body = b'{"model": "openai/text-embedding-3-small", "input": "fox"}'

    response = await AsyncClient().post(
        path=URL, data=body, content_type="application/json", headers=AUTH
    )

    assert response.status_code == 200
    assert response.json() == EMBEDDINGS
    assert upstream[0].url == f"{UPSTREAM_URL}/embeddings"
    assert upstream[0].content == body
    fields = metrics_line(caplog=caplog)
    assert fields["endpoint"] == "embeddings"
    assert fields["model"] == "openai/text-embedding-3-small"
    assert fields["prompt_tokens"] == 4
    assert fields["cost"] == 0.00000008


async def test_rejects_unknown_key(upstream) -> None:
    response = await AsyncClient().post(
        path=URL,
        data={"model": "m", "input": "fox"},
        content_type="application/json",
        headers={"Authorization": "Bearer wrong"},
    )

    assert response.status_code == 401
    assert upstream == []


async def test_proxies_embedding_models_page(upstream) -> None:
    models = {"data": [{"id": "openai/text-embedding-3-small"}]}
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=models)
    )

    response = await AsyncClient().get(
        path=f"{reverse('api:embeddings:models')}?limit=1&offset=2",
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json() == models
    assert upstream[0].url == (
        f"{UPSTREAM_URL}/embeddings/models?limit=1&offset=2"
    )
