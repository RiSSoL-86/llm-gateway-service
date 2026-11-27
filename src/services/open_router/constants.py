# Paths from the base URL in settings, the same as OpenRouter ones
CHAT_COMPLETIONS_PATH = "chat/completions"
COMPLETIONS_PATH = "completions"
RESPONSES_PATH = "responses"
MESSAGES_PATH = "messages"
EMBEDDINGS_PATH = "embeddings"
EMBEDDING_MODELS_PATH = "embeddings/models"
MODELS_PATH = "models"
MODELS_COUNT_PATH = "models/count"
MODEL_ENDPOINTS_PATH = "models/{author}/{slug}/endpoints"
GENERATION_PATH = "generation"
# Idle connections live this long, so the next request skips the TLS handshake
KEEPALIVE_EXPIRY = 60

# Server-sent events of OpenRouter streams
SSE_DATA_PREFIX = b"data:"
SSE_DONE = b"[DONE]"
# A chat delta with one of these is a real token: the role-only one is not
TOKEN_DELTA_FIELDS = ("content", "reasoning", "tool_calls")
# The text completion field of a choice
TOKEN_TEXT_FIELD = "text"
# `responses` and `messages` streams: tokens in a top-level `delta`
DELTA_FIELD = "delta"
DELTA_TOKEN_FIELDS = ("text", "thinking", "partial_json")
# Events of those streams keep `id`, `model`, `usage` in this inner answer
INNER_ANSWER_FIELDS = ("response", "message")
ERROR_EVENT_TYPE = "error"
MAX_ERROR_LENGTH = 300
# Bigger JSON answers are not parsed whole, only their own small fields
LARGE_ANSWER_BYTES = 1024 * 1024
ANSWER_FIELDS = (b"id", b"model", b"provider", b"usage", b"error")
# Enough for any of those fields, `usage` with its details too
MAX_FIELD_BYTES = 8192
