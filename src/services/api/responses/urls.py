from dmr.routing import Router, path

from services.api.responses.controllers import ResponsesController

# OpenAI clients call `<base_url>/responses`, no trailing slash
router = Router(
    prefix="v1/",
    urls=[
        path(
            "responses",
            ResponsesController.as_view(),
            name="responses",
        ),
    ],
)
