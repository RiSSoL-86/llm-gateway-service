import sys

from django_project.settings import env

# `manage.py test` puts "test" in argv; pytest does not, so it is detected
# via its imported module (present once the test session has started).
RUNNING_TESTS = (
    env.bool("DJANGO_TESTING", default=False)
    or "test" in sys.argv
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
