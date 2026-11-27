from django.urls import include
from dmr.routing import Router, path

from services.api.chat_completions import urls as chat_completions_urls
from services.api.completions import urls as completions_urls
from services.api.embeddings import urls as embeddings_urls
from services.api.generation import urls as generation_urls
from services.api.messages import urls as messages_urls
from services.api.models import urls as models_urls
from services.api.responses import urls as responses_urls

router = Router(
    prefix="",
    urls=[
        path(
            module.router.prefix,
            include(
                (module.router.urls, namespace),
                namespace=namespace,
            ),
        )
        for namespace, module in (
            ("chat_completions", chat_completions_urls),
            ("completions", completions_urls),
            ("responses", responses_urls),
            ("messages", messages_urls),
            ("embeddings", embeddings_urls),
            ("models", models_urls),
            ("generation", generation_urls),
        )
    ],
)
