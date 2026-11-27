import sys

from django_project.settings import env

# `test` as the manage.py command itself, or pytest once it is imported
RUNNING_TESTS = (
    env.bool("DJANGO_TESTING", default=False)
    or sys.argv[1:2] == ["test"]
    or "pytest" in sys.modules
)

if RUNNING_TESTS:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        },
    }
    OPENROUTER_BASE_URL = "https://upstream.test/api/v1"
    OPENROUTER_API_KEY = "sk-or-real-key"
    GATEWAY_KEYS = {"sk-gw-test": "tester"}
