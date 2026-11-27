from dmr.routing import Router, path

from services.api.models.controllers import ModelsController

# OpenAI clients call `<base_url>/models`, no trailing slash
router = Router(
    prefix="v1/",
    urls=[
        path(
            "models",
            ModelsController.as_view(),
            name="models",
        ),
    ],
)
