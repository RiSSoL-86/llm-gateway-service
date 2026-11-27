import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")

application = get_asgi_application()

# Warm the shared OpenRouter client up: its TLS setup takes ~150 ms,
# the first client request should not pay for it.
from services.open_router.client import OpenRouterClient  # noqa: E402

OpenRouterClient.get()
