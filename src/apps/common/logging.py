import json
import logging
from datetime import UTC, datetime
from typing import Any, final, override


@final
class JsonFormatter(logging.Formatter):
    """Format a log record as one JSON line, `extra={"fields": ...}` on top."""

    def __init__(self, service: str = "llm-gateway-service") -> None:
        """Take the service name every line is marked with."""
        super().__init__()
        self.service = service

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Render the record with its extra fields."""
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=UTC
            ).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "service": self.service,
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(fields)
        if record.exc_info:
            payload["exception"] = self.formatException(ei=record.exc_info)
        return json.dumps(obj=payload, default=str, ensure_ascii=False)
