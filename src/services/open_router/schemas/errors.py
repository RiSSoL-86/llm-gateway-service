from typing import final

from pydantic import BaseModel


@final
class ErrorDetail(BaseModel):
    """Carry the error message the way OpenRouter does."""

    message: str
    code: int | str | None = None


@final
class ErrorResponse(BaseModel):
    """Wrap an error in the OpenAI format: clients read `error.message`."""

    error: ErrorDetail
