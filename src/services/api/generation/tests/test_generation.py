import httpx
from django.test import AsyncClient
from django.urls import reverse

from services.api.common.tests.constants import AUTH
from services.open_router.tests.mock import UPSTREAM_URL

URL = reverse("api:generation:generation")

GENERATION = {"data": {"id": "gen-1", "total_cost": 0.0001}}


async def test_proxies_generation_stats(upstream) -> None:
    upstream.install(
        handler=lambda _: httpx.Response(status_code=200, json=GENERATION)
    )

    response = await AsyncClient().get(path=f"{URL}?id=gen-1", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == GENERATION
    assert upstream[0].url == f"{UPSTREAM_URL}/generation?id=gen-1"


async def test_passes_not_found_through(upstream) -> None:
    error = {"error": {"code": 404, "message": "Generation not found"}}
    upstream.install(
        handler=lambda _: httpx.Response(status_code=404, json=error)
    )

    response = await AsyncClient().get(path=f"{URL}?id=gen-x", headers=AUTH)

    assert response.status_code == 404
    assert response.json() == error


async def test_leaves_missing_id_to_openrouter(upstream) -> None:
    error = {"error": {"code": 400, "message": "id is required"}}
    upstream.install(
        handler=lambda _: httpx.Response(status_code=400, json=error)
    )

    response = await AsyncClient().get(path=URL, headers=AUTH)

    assert response.status_code == 400
    assert response.json() == error
    assert upstream[0].url == f"{UPSTREAM_URL}/generation"
