import json
from typing import TYPE_CHECKING, final

from services.open_router.constants import (
    MAX_ERROR_LENGTH,
    SSE_DATA_PREFIX,
    SSE_DONE,
    TOKEN_DELTA_FIELDS,
    TOKEN_TEXT_FIELD,
)

if TYPE_CHECKING:
    from services.open_router.schemas import OpenRouterAnswer


@final
class AnswerSniffer:
    """Read a copy of an OpenRouter answer, the bytes themselves stay as is."""

    __slots__ = ("_tail", "answer")

    def __init__(self, answer: OpenRouterAnswer) -> None:
        """Take the answer the findings are written to."""
        self.answer = answer
        self._tail = b""

    def feed(self, chunk: bytes) -> None:
        """Take the next raw chunk of a server-sent events stream."""
        if b"\n" not in chunk:
            self._tail += chunk
            return
        lines = (self._tail + chunk).split(b"\n")
        self._tail = lines.pop()
        for line in lines:
            self._inspect_line(line=line)

    def finish(self) -> None:
        """Inspect the last line if the stream did not end with a newline."""
        if self._tail:
            self._inspect_line(line=self._tail)
            self._tail = b""

    def inspect_json(self, payload: bytes) -> None:
        """Take a whole JSON answer or one event of the stream."""
        try:
            event = json.loads(s=payload)
        except ValueError:
            return
        if not isinstance(event, dict):
            return
        answer = self.answer
        answer.generation_id = answer.generation_id or self._text(
            value=event.get("id")
        )
        answer.model = answer.model or self._text(value=event.get("model"))
        answer.provider = answer.provider or self._text(
            value=event.get("provider")
        )
        usage = event.get("usage")
        if isinstance(usage, dict):
            answer.usage = usage
        if not answer.seen_token:
            answer.seen_token = self._has_token(choices=event.get("choices"))
        error = event.get("error")
        if isinstance(error, dict):
            message = self._text(value=error.get("message"))
            answer.error = (message or json.dumps(obj=error))[
                :MAX_ERROR_LENGTH
            ]
        elif error:
            # Not OpenRouter itself, e.g. Cloudflare: `{"error": "..."}`
            answer.error = str(error)[:MAX_ERROR_LENGTH]

    def _inspect_line(self, line: bytes) -> None:
        # Comments (`: OPENROUTER PROCESSING`) and blank lines are skipped
        if not line.startswith(SSE_DATA_PREFIX):
            return
        payload = line[len(SSE_DATA_PREFIX) :].strip()
        if not payload or payload == SSE_DONE:
            return
        self.answer.seen_data = True
        # JSON only up to the first token and for `usage` / `error` events
        if (
            not self.answer.seen_token
            or b'"usage"' in payload
            or b'"error"' in payload
        ):
            self.inspect_json(payload=payload)

    @staticmethod
    def _has_token(choices: object) -> bool:
        if not isinstance(choices, list):
            return False
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            if choice.get(TOKEN_TEXT_FIELD):
                return True
            delta = choice.get("delta")
            if isinstance(delta, dict) and any(
                delta.get(field) for field in TOKEN_DELTA_FIELDS
            ):
                return True
        return False

    @staticmethod
    def _text(value: object) -> str | None:
        return value if isinstance(value, str) and value else None
