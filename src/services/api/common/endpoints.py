from typing import TYPE_CHECKING, ClassVar, final, override

from dmr.endpoint import Endpoint
from dmr.exceptions import NotAcceptableError
from dmr.negotiation import ResponseNegotiator

if TYPE_CHECKING:
    from django.http import HttpRequest
    from dmr.renderers import Renderer


@final
class AnyAcceptNegotiator(ResponseNegotiator):
    """Take any `Accept`: the answer is OpenRouter's, not rendered by us."""

    __slots__ = ()

    @override
    def __call__(self, request: HttpRequest) -> Renderer:
        """Pick the renderer of our own errors, JSON if none is accepted."""
        try:
            return super().__call__(request=request)
        except NotAcceptableError:
            request.__dmr_renderer__ = self._default  # type: ignore[attr-defined]
            return self._default


class GatewayEndpoint(Endpoint):
    """Endpoint that never turns a request away by its `Accept`."""

    response_negotiator_cls: ClassVar[type[ResponseNegotiator]] = (
        AnyAcceptNegotiator
    )
