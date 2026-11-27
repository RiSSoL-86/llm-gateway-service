from django_project.settings import env

# Upstream: real OpenRouter, or the mock of the load test (stage 2)
OPENROUTER_BASE_URL = env(
    "OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1"
)

# Our real OpenRouter key: the gateway swaps the client key for it
OPENROUTER_API_KEY = env("OPENROUTER_API_KEY", default="")

# Client keys: `our-key=client-name,other-key=other-name`, spaces dropped
GATEWAY_KEYS: dict[str, str] = {
    key.strip(): name.strip()
    for key, name in env.dict("GATEWAY_KEYS", default={}).items()
}

# One shared HTTP client per worker, long reads for slow models
UPSTREAM_CONNECT_TIMEOUT = env.float("UPSTREAM_CONNECT_TIMEOUT", default=10)
UPSTREAM_READ_TIMEOUT = env.float("UPSTREAM_READ_TIMEOUT", default=300)
UPSTREAM_MAX_CONNECTIONS = env.int("UPSTREAM_MAX_CONNECTIONS", default=1000)

# Long chats and base64 images go well past Django's 2.5 MB default
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int(
    "DATA_UPLOAD_MAX_MEMORY_SIZE", default=50 * 1024 * 1024
)
