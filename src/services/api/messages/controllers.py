from http import HTTPStatus
from typing import final

from django.http import HttpResponseBase
from dmr import ResponseSpec, validate

from services.api.common.components import BodyDocs
from services.api.common.constants import UPSTREAM_ERROR_SPECS
from services.api.common.controllers import GatewayController
from services.api.messages.schemas import MessageRequest, MessageResponse
from services.api.messages.services.message import MessageService


@final
class MessagesController(GatewayController):
    """Serve OpenRouter `POST /api/v1/messages` behind our keys."""

    @validate(
        ResponseSpec(
            return_type=MessageResponse,
            status_code=HTTPStatus.OK,
            description=(
                "JSON answer. With `stream: true` Anthropic server-sent "
                "events: `message_start`, `content_block_delta`, ..., "
                "`message_stop`."
            ),
        ),
        *UPSTREAM_ERROR_SPECS,
        tags=["Messages"],
        summary="Anthropic Messages API answer, the same as OpenRouter",
    )
    async def post(
        self,
        body_docs: BodyDocs[MessageRequest],
    ) -> HttpResponseBase:
        """Take the Messages API request and give it to its service."""
        return await MessageService().execute(
            client=self.client,
            query=self.query,
            body=self.request.body,
            headers=self.request.headers,
        )
