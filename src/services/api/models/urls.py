from dmr.routing import Router, path

from services.api.models.controllers import (
    ModelEndpointsController,
    ModelsController,
    ModelsCountController,
)

# OpenAI clients call `<base_url>/models`, no trailing slash
router = Router(
    prefix="v1/",
    urls=[
        path(
            "models",
            ModelsController.as_view(),
            name="models",
        ),
        path(
            "models/count",
            ModelsCountController.as_view(),
            name="count",
        ),
        path(
            "models/<str:author>/<str:slug>/endpoints",
            ModelEndpointsController.as_view(),
            name="endpoints",
        ),
    ],
)
