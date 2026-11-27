from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path
from django.views.static import serve
from dmr.openapi import OpenAPIConfig, build_schema
from dmr.openapi.views import OpenAPIJsonView, SwaggerView
from dmr.plugins.pydantic import PydanticSerializer
from dmr.routing import Router, build_404_handler, build_500_handler, path

from services.api import urls as api_urls

if TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

router = Router(
    prefix="api/",
    urls=api_urls.router.urls,
)

schema = build_schema(
    router,
    config=OpenAPIConfig(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description=(
            "OpenRouter-compatible gateway. Point any OpenAI/OpenRouter "
            "client at `<host>/api/v1` and use the gateway key."
        ),
    ),
)
handler404 = build_404_handler(router.prefix, serializer=PydanticSerializer)
handler500 = build_500_handler(router.prefix, serializer=PydanticSerializer)

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path(
        router.prefix,
        include(
            (router.urls, "api"),
            namespace="api",
        ),
    ),
    path(
        f"{router.prefix}docs/",
        SwaggerView.as_view(schema),
        name="docs",
    ),
    path(
        f"{router.prefix}schema.json",
        OpenAPIJsonView.as_view(schema),
        name="schema-json",
    ),
    # Admin static files only: no extra server or sync middleware for that
    re_path(
        r"^static/(?P<path>.*)$",
        serve,
        {"document_root": settings.STATIC_ROOT},
    ),
]
