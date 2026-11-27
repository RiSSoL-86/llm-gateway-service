import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")

application = get_asgi_application()

# Warm the OpenRouter client up: the first request skips the ~150 ms TLS
from services.open_router.client import OpenRouterClient  # noqa: E402

OpenRouterClient.get()
