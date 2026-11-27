from typing import Any, final

from apps.common.schemas import PermissiveModel


@final
class ModelsResponse(PermissiveModel):
    """Describe the OpenRouter model list, passed through unchanged."""

    data: list[dict[str, Any]]
