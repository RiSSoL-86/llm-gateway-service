import json
import logging

from apps.common.logging import JsonFormatter


def test_line_is_json_with_fields() -> None:
    record = logging.LogRecord(
        name="x",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="msg",
        args=None,
        exc_info=None,
    )
    record.fields = {"event": "proxy", "ttft_ms": 1.5}

    line = json.loads(s=JsonFormatter(service="s").format(record=record))

    assert line["level"] == "INFO"
    assert line["service"] == "s"
    assert line["ttft_ms"] == 1.5
