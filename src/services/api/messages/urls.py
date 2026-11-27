from dmr.routing import Router, path

from services.api.messages.controllers import MessagesController

# Anthropic clients call `<base_url>/v1/messages`, base URL `<host>/api`
router = Router(
    prefix="v1/",
    urls=[
        path(
            "messages",
            MessagesController.as_view(),
            name="messages",
        ),
    ],
)
