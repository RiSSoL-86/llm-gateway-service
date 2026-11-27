# Paths from the base URL in settings, the same as OpenRouter ones
CHAT_COMPLETIONS_PATH = "chat/completions"
COMPLETIONS_PATH = "completions"
EMBEDDINGS_PATH = "embeddings"
MODELS_PATH = "models"
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
MAX_ERROR_LENGTH = 300
