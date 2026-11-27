import json
from typing import TYPE_CHECKING, Any, ClassVar, final

from services.open_router.constants import (
    ANSWER_FIELDS,
    DELTA_FIELD,
    DELTA_TOKEN_FIELDS,
    ERROR_EVENT_TYPE,
    INNER_ANSWER_FIELDS,
    LARGE_ANSWER_BYTES,
    MAX_ERROR_LENGTH,
    MAX_FIELD_BYTES,
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

    __slots__ = ("_pieces", "answer")

    _decoder: ClassVar = json.JSONDecoder()

    def __init__(self, answer: OpenRouterAnswer) -> None:
        """Take the answer the findings are written to."""
        self.answer = answer
        # Pieces of the line not ended yet: joined once, at its newline
        self._pieces: list[bytes] = []

    def feed(self, chunk: bytes) -> None:
        """Take the next raw chunk of a server-sent events stream."""
        self._pieces.append(chunk)
        if b"\n" not in chunk:
            return
        lines = b"".join(self._pieces).split(b"\n")
        self._pieces = [lines.pop()]
        for line in lines:
            self._inspect_line(line=line)

    def finish(self) -> None:
        """Inspect the last line if the stream did not end with a newline."""
        tail = b"".join(self._pieces)
        self._pieces = []
        if tail:
            self._inspect_line(line=tail)

    def inspect_json(self, payload: bytes) -> None:
        """Take a whole JSON answer or one event of the stream."""
        if len(payload) > LARGE_ANSWER_BYTES:
            event = self._answer_fields(payload=payload)
        else:
            try:
                event = json.loads(s=payload)
            except ValueError:
                return
        if not isinstance(event, dict):
            return
        self._read_event(event=event)
        for field in INNER_ANSWER_FIELDS:
            inner = event.get(field)
            if isinstance(inner, dict):
                self._read_event(event=inner)
        if not self.answer.seen_token:
            self.answer.seen_token = self._has_delta_token(
                delta=event.get(DELTA_FIELD)
            )
        if event.get("type") == ERROR_EVENT_TYPE and not self.answer.error:
            # A `responses` stream error: its message is top-level
            self.answer.error = str(event.get("message") or event)[
                :MAX_ERROR_LENGTH
            ]

    def _read_event(self, event: dict[str, Any]) -> None:
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
            # `messages` streams send input tokens first, output ones last
            answer.usage = (answer.usage or {}) | usage
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

    @classmethod
    def _answer_fields(cls, payload: bytes) -> dict[str, Any]:
        # Not parsed whole: the first match of a key is OpenRouter's own field
        fields: dict[str, Any] = {}
        for field in ANSWER_FIELDS:
            key = b'"' + field + b'":'
            start = payload.find(key)
            if start < 0:
                continue
            start += len(key)
            value = payload[start : start + MAX_FIELD_BYTES]
            try:
                fields[field.decode()], _ = cls._decoder.raw_decode(
                    s=value.decode(errors="ignore").lstrip()
                )
            except ValueError:
                continue
        return fields

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
    def _has_delta_token(delta: object) -> bool:
        # `responses`: the text itself; `messages`: a text, thinking or tool
        if isinstance(delta, str):
            return bool(delta)
        return isinstance(delta, dict) and any(
            delta.get(field) for field in DELTA_TOKEN_FIELDS
        )

    @staticmethod
    def _text(value: object) -> str | None:
        return value if isinstance(value, str) and value else None
