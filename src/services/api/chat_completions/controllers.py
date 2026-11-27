from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import ResponseSpec, validate

from services.api.chat_completions.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from services.api.chat_completions.services.chat_completion import (
    ChatCompletionService,
)
from services.api.common.components import BodyDocs
from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController


@final
class ChatCompletionsController(GatewayController):
    """Serve OpenRouter `POST /api/v1/chat/completions` behind our keys."""

    @validate(
        ResponseSpec(
            return_type=ChatCompletionResponse,
            status_code=HTTPStatus.OK,
            description=(
                "JSON answer. With `stream: true` server-sent events: "
                "`data: {chunk}` lines, the last one is `data: [DONE]`."
            ),
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Chat"],
        summary="Chat completion, the same as OpenRouter",
    )
    async def post(
        self,
        body_docs: BodyDocs[ChatCompletionRequest],
    ) -> HttpResponseBase:
        """Take the chat completion request and give it to its service."""
        return await ChatCompletionService().execute(
            client=self.client,
            query=self.query,
            body=self.request.body,
            headers=self.request.headers,
        )
