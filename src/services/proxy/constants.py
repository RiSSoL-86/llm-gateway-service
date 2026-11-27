# Client headers OpenRouter understands, the rest stays with us
FORWARDED_REQUEST_HEADERS = ("HTTP-Referer", "X-Title")
# ASGI header bytes come to Django decoded as this
HEADER_ENCODING = "latin-1"
# OpenRouter headers the client backs off by, the rest stays with us
FORWARDED_RESPONSE_HEADERS = frozenset({"retry-after"})
RATE_LIMIT_HEADER_PREFIX = "x-ratelimit-"
EVENT_STREAM = "text/event-stream"
# Nothing on the way may hold server-sent events back
STREAM_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
# OpenRouter errors carry the id of our account: not for clients
ACCOUNT_FIELD = "user_id"

# Metric event of one proxied request, of any endpoint
METRICS_EVENT = "proxy"

UPSTREAM_AUTH_FAILED = "Gateway upstream auth failed"
UPSTREAM_UNAVAILABLE = "Upstream is unavailable"
UPSTREAM_STREAM_BROKE = "Upstream stream broke"
