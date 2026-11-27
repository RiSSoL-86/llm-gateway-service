from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import Path, ResponseSpec, validate

from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController
from services.api.models.schemas import (
    ModelEndpointsResponse,
    ModelPath,
    ModelsCountResponse,
    ModelsResponse,
)
from services.api.models.services.model_endpoints import (
    ModelEndpointsService,
)
from services.api.models.services.models import ModelsService
from services.api.models.services.models_count import ModelsCountService
from services.open_router.schemas import ErrorResponse


@final
class ModelsController(GatewayController):
    """Serve OpenRouter `GET /api/v1/models` behind our keys."""

    @validate(
        ResponseSpec(
            return_type=ModelsResponse,
            status_code=HTTPStatus.OK,
            description="Query parameters go to OpenRouter as they are.",
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Models"],
        summary="Models with prices and limits, the same as OpenRouter",
    )
    async def get(self) -> HttpResponseBase:
        """Take the model list request and give it to its service."""
        return await ModelsService().execute(
            client=self.client,
            query=self.query,
            headers=self.request.headers,
        )


@final
class ModelsCountController(GatewayController):
    """Serve OpenRouter `GET /api/v1/models/count` behind our keys."""

    @validate(
        ResponseSpec(
            return_type=ModelsCountResponse,
            status_code=HTTPStatus.OK,
            description="Query parameters go to OpenRouter as they are.",
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Models"],
        summary="Number of models, the same as OpenRouter",
    )
    async def get(self) -> HttpResponseBase:
        """Take the model count request and give it to its service."""
        return await ModelsCountService().execute(
            client=self.client,
            query=self.query,
            headers=self.request.headers,
        )


@final
class ModelEndpointsController(GatewayController):
    """Serve OpenRouter `GET /api/v1/models/{author}/{slug}/endpoints`."""

    @validate(
        ResponseSpec(
            return_type=ModelEndpointsResponse, status_code=HTTPStatus.OK
        ),
        ResponseSpec(
            return_type=ErrorResponse, status_code=HTTPStatus.NOT_FOUND
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Models"],
        summary="Providers of one model with prices, the same as OpenRouter",
    )
    async def get(self, parsed_path: Path[ModelPath]) -> HttpResponseBase:
        """Take the model providers request and give it to its service."""
        return await ModelEndpointsService().execute(
            client=self.client,
            author=parsed_path.author,
            slug=parsed_path.slug,
            query=self.query,
            headers=self.request.headers,
        )
