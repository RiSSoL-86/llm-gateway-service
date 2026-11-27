from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import Body, ResponseSpec, validate

from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController
from services.api.completions.schemas import (
    CompletionRequest,
    CompletionResponse,
)
from services.api.completions.services.completion import CompletionService


@final
class CompletionsController(GatewayController):
    """Serve OpenRouter `POST /api/v1/completions` behind our keys."""

    @validate(
        ResponseSpec(
            return_type=CompletionResponse,
            status_code=HTTPStatus.OK,
            description=(
                "JSON answer. With `stream: true` server-sent events: "
                "`data: {chunk}` lines, the last one is `data: [DONE]`."
            ),
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Completions"],
        summary="Text completion by a prompt, the same as OpenRouter",
    )
    async def post(
        self,
        parsed_body: Body[CompletionRequest],
    ) -> HttpResponseBase:
        """Take the text completion request and give it to its service."""
        return await CompletionService().execute(
            client=self.client,
            body=self.request.body,
            headers=self.request.headers,
            model=parsed_body.model,
            stream=parsed_body.stream,
        )
