from typing import final

from pydantic import ValidationError

from services.open_router.schemas import OpenRouterRequest


@final
class RequestReader:
    """Read the metrics fields of a raw request, never failing on it."""

    @staticmethod
    def read(body: bytes) -> OpenRouterRequest:
        """Return `model` and `stream`, defaults if the body is not as such."""
        try:
            return OpenRouterRequest.model_validate_json(json_data=body)
        except ValidationError:
            # Not ours to reject: OpenRouter answers it with its own error
            return OpenRouterRequest()
