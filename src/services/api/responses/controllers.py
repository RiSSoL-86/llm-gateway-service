from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import ResponseSpec, validate

from services.api.common.components import BodyDocs
from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController
from services.api.responses.schemas import ResponseRequest, ResponseResponse
from services.api.responses.services.response import ResponseService


@final
class ResponsesController(GatewayController):
    """Serve OpenRouter `POST /api/v1/responses` behind our keys."""

    @validate(
        ResponseSpec(
            return_type=ResponseResponse,
            status_code=HTTPStatus.OK,
            description=(
                "JSON answer. With `stream: true` server-sent events: "
                "`response.created`, `response.output_text.delta`, ..., "
                "`response.completed`."
            ),
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Responses"],
        summary="OpenAI Responses API answer, the same as OpenRouter",
    )
    async def post(
        self,
        body_docs: BodyDocs[ResponseRequest],
    ) -> HttpResponseBase:
        """Take the Responses API request and give it to its service."""
        return await ResponseService().execute(
            client=self.client,
            query=self.query,
            body=self.request.body,
            headers=self.request.headers,
        )
