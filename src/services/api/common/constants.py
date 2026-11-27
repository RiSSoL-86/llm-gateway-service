from http import HTTPStatus

from dmr import ResponseSpec

from services.open_router.schemas import ErrorResponse

SECURITY_SCHEME_NAME = "GatewayKey"
BEARER_SCHEME = "bearer"
INVALID_KEY = "Invalid API key"

# Errors OpenRouter or the proxy answer on any endpoint, for the API docs
UPSTREAM_ERROR_SPECS = tuple(
    ResponseSpec(return_type=ErrorResponse, status_code=status)
    for status in (
        HTTPStatus.BAD_REQUEST,
        HTTPStatus.PAYMENT_REQUIRED,
        HTTPStatus.TOO_MANY_REQUESTS,
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.GATEWAY_TIMEOUT,
    )
)
