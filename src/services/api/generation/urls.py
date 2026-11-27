from dmr.routing import Router, path

from services.api.generation.controllers import GenerationController

# OpenRouter clients call `<base_url>/generation?id=...`
router = Router(
    prefix="v1/",
    urls=[
        path(
            "generation",
            GenerationController.as_view(),
            name="generation",
        ),
    ],
)
