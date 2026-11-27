from dmr.routing import Router, path

from services.api.completions.controllers import CompletionsController

# OpenAI clients call `<base_url>/completions`, no trailing slash
router = Router(
    prefix="v1/",
    urls=[
        path(
            "completions",
            CompletionsController.as_view(),
            name="completions",
        ),
    ],
)
