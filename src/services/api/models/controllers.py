from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import ResponseSpec, validate

from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController
from services.api.models.schemas import ModelsResponse
from services.api.models.services.models import ModelsService


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
