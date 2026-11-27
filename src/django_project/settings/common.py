from django_project.settings import (
    BASE_DIR,
    ENVIRONMENT,
    ENVIRONMENT_LOCAL,
    env,
)

DEBUG = env.bool("DEBUG")

if DEBUG and ENVIRONMENT != ENVIRONMENT_LOCAL:
    raise ValueError("DEBUG mode is allowed only in the local environment")

SECRET_KEY = env("SECRET_KEY")
if SECRET_KEY.startswith("dev-only") and ENVIRONMENT != ENVIRONMENT_LOCAL:
    raise ValueError("Set a random SECRET_KEY outside the local environment")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = [
    origin for origin in env.list("CSRF_TRUSTED_ORIGINS", default=[]) if origin
]

# Async middleware only: a sync one pushes each request through a thread
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "django_project.urls"
ASGI_APPLICATION = "django_project.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Caddy terminates HTTPS in front of the app
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

PROJECT_NAME = env("PROJECT_NAME")
