from abc import ABC, abstractmethod
from typing import Any


class BaseService(ABC):
    """Base class for one business operation."""

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run the operation."""
