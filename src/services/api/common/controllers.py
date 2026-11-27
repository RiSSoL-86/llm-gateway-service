from typing import Any, override

from dmr import Controller
from dmr.errors import ErrorType
from dmr.plugins.pydantic import PydanticSerializer

from services.api.common.auth import GatewayKeyAuth
from services.api.common.endpoints import GatewayEndpoint
from services.open_router.schemas import ErrorDetail, ErrorResponse


class GatewayController(Controller[PydanticSerializer]):
    """Base of every OpenRouter-like endpoint: gateway key, OpenAI errors."""

    auth = (GatewayKeyAuth(),)
    endpoint_cls = GatewayEndpoint
    error_model = ErrorResponse
    # The answer is OpenRouter's own bytes: nothing of ours to validate
    validate_responses = False

    @property
    def client(self) -> str:
        """Return the client name of the gateway key, checked by `auth`."""
        return GatewayKeyAuth.client_of(request=self.request) or ""

    @property
    def query(self) -> str:
        """Return the raw query string of the request."""
        return str(self.request.META.get("QUERY_STRING", ""))

    @override
    def format_error(
        self,
        error: str | Exception,
        *,
        loc: str | list[str | int] | None = None,
        error_type: str | ErrorType | None = None,
    ) -> Any:
        """Put our own errors in the OpenAI format, like OpenRouter ones."""
        # The `*` is DMR's: an override keeps the signature of its parent
        formatted = super().format_error(
            error=error, loc=loc, error_type=error_type
        )
        details = (
            formatted.get("detail") if isinstance(formatted, dict) else None
        )
        messages = [
            self._message(detail=detail)
            for detail in details or []
            if isinstance(detail, dict)
        ]
        message = "; ".join(messages) or str(error)
        return ErrorResponse(error=ErrorDetail(message=message)).model_dump(
            exclude_none=True
        )

    @staticmethod
    def _message(detail: dict[str, Any]) -> str:
        # `loc` starts with the DMR component (`parsed_body`): not for clients
        field = ".".join(str(part) for part in detail.get("loc", [])[1:])
        message = str(detail.get("msg"))
        return f"{field}: {message}" if field else message
