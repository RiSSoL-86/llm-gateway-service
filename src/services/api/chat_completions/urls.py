from dmr.routing import Router, path

from services.api.chat_completions.controllers import (
    ChatCompletionsController,
)

# OpenAI clients call `<base_url>/chat/completions`, no trailing slash
router = Router(
    prefix="v1/chat/",
    urls=[
        path(
            "completions",
            ChatCompletionsController.as_view(),
            name="completions",
        ),
    ],
)
