from typing import TYPE_CHECKING, Self, final, override

from django.conf import settings
from dmr.exceptions import NotAuthenticatedError
from dmr.openapi.objects import SecurityRequirement, SecurityScheme
from dmr.security.base import AsyncAuth

from services.api.common.constants import (
    BEARER_SCHEME,
    INVALID_KEY,
    SECURITY_SCHEME_NAME,
)

if TYPE_CHECKING:
    from django.http import HttpRequest
    from dmr.controller import Controller
    from dmr.endpoint import Endpoint
    from dmr.openapi.objects import Reference
    from dmr.serializer import BaseSerializer


@final
class GatewayKeyAuth(AsyncAuth):
    """Let in `Authorization: Bearer <key>` with a key from settings."""

    __slots__ = ()

    @staticmethod
    def client_of(request: HttpRequest) -> str | None:
        """Return the client name of the gateway key in `Authorization`."""
        header = request.headers.get("Authorization", "")
        scheme, _, key = header.partition(" ")
        if scheme.lower() != BEARER_SCHEME or not key:
            return None
        keys: dict[str, str] = settings.GATEWAY_KEYS  # type: ignore[misc]
        return keys.get(key.strip())

    @override
    async def __call__(
        self,
        endpoint: Endpoint,
        controller: Controller[BaseSerializer],
    ) -> Self | None:
        """Let the request in only with a known gateway key."""
        if self.client_of(request=controller.request) is None:
            raise NotAuthenticatedError(msg=INVALID_KEY)
        return self

    @property
    @override
    def security_schemes(self) -> dict[str, SecurityScheme | Reference]:
        """Describe the Swagger `Authorize` button the gateway key goes in."""
        return {
            SECURITY_SCHEME_NAME: SecurityScheme(
                type="http",
                scheme=BEARER_SCHEME,
                description="Gateway key, the same way as an OpenRouter key",
            ),
        }

    @property
    @override
    def security_requirement(self) -> SecurityRequirement:
        """Require the gateway key on every endpoint."""
        return {SECURITY_SCHEME_NAME: []}

    @property
    @override
    def www_authenticate_challenge(self) -> str | None:
        """Tell clients to send a bearer token."""
        return "Bearer"
