from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import Body, ResponseSpec, validate

from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController
from services.api.embeddings.schemas import (
    EmbeddingRequest,
    EmbeddingResponse,
)
from services.api.embeddings.services.embedding import EmbeddingService


@final
class EmbeddingsController(GatewayController):
    """Serve OpenRouter `POST /api/v1/embeddings` behind our keys."""

    @validate(
        ResponseSpec(return_type=EmbeddingResponse, status_code=HTTPStatus.OK),
        *UPSTREAM_ERROR_SPECS,
        tags=["Embeddings"],
        summary="Embeddings of texts, the same as OpenRouter",
    )
    async def post(
        self,
        parsed_body: Body[EmbeddingRequest],
    ) -> HttpResponseBase:
        """Take the embeddings request and give it to its service."""
        return await EmbeddingService().execute(
            client=self.client,
            body=self.request.body,
            headers=self.request.headers,
            model=parsed_body.model,
        )
