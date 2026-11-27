from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import ResponseSpec, validate

from services.api.common.components import BodyDocs, QueryDocs
from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController
from services.api.embeddings.schemas import (
    EmbeddingModelsQuery,
    EmbeddingModelsResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from services.api.embeddings.services.embedding import EmbeddingService
from services.api.embeddings.services.embedding_models import (
    EmbeddingModelsService,
)


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
        body_docs: BodyDocs[EmbeddingRequest],
    ) -> HttpResponseBase:
        """Take the embeddings request and give it to its service."""
        return await EmbeddingService().execute(
            client=self.client,
            query=self.query,
            body=self.request.body,
            headers=self.request.headers,
        )


@final
class EmbeddingModelsController(GatewayController):
    """Serve OpenRouter `GET /api/v1/embeddings/models` behind our keys."""

    @validate(
        ResponseSpec(
            return_type=EmbeddingModelsResponse, status_code=HTTPStatus.OK
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Embeddings"],
        summary="Embedding models with prices, the same as OpenRouter",
    )
    async def get(
        self,
        query_docs: QueryDocs[EmbeddingModelsQuery],
    ) -> HttpResponseBase:
        """Take the embedding model list request and give it to its service."""
        return await EmbeddingModelsService().execute(
            client=self.client,
            query=self.query,
            headers=self.request.headers,
        )
