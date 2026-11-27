from enum import StrEnum
from typing import final


@final
class Outcome(StrEnum):
    """Tell how a proxied request ended."""

    OK = "ok"
    UPSTREAM_ERROR = "upstream_error"
    UPSTREAM_UNAVAILABLE = "upstream_unavailable"
    STREAM_ERROR = "stream_error"
    CLIENT_DISCONNECTED = "client_disconnected"
