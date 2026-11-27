from dmr.routing import Router, path

from services.api.embeddings.controllers import (
    EmbeddingModelsController,
    EmbeddingsController,
)

# OpenAI clients call `<base_url>/embeddings`, no trailing slash
router = Router(
    prefix="v1/",
    urls=[
        path(
            "embeddings",
            EmbeddingsController.as_view(),
            name="embeddings",
        ),
        path(
            "embeddings/models",
            EmbeddingModelsController.as_view(),
            name="models",
        ),
    ],
)
