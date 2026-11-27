from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import ResponseSpec, validate

from services.api.common.components import QueryDocs
from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController
from services.api.generation.schemas import (
    GenerationQuery,
    GenerationResponse,
)
from services.api.generation.services.generation import GenerationService
from services.open_router.schemas import ErrorResponse


@final
class GenerationController(GatewayController):
    """Serve OpenRouter `GET /api/v1/generation` behind our keys."""

    @validate(
        ResponseSpec(
            return_type=GenerationResponse, status_code=HTTPStatus.OK
        ),
        ResponseSpec(
            return_type=ErrorResponse, status_code=HTTPStatus.NOT_FOUND
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Generation"],
        summary="Cost and tokens of one generation, the same as OpenRouter",
    )
    async def get(
        self,
        query_docs: QueryDocs[GenerationQuery],
    ) -> HttpResponseBase:
        """Take the generation stats request and give it to its service."""
        return await GenerationService().execute(
            client=self.client,
            query=self.query,
            headers=self.request.headers,
        )
