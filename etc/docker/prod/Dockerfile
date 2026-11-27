FROM ghcr.io/astral-sh/uv:0.11.17 AS uv

FROM python:3.14-slim

COPY --from=uv /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=django_project.settings \
    PORT=8000 \
    WEB_CONCURRENCY=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project
COPY src ./

# Admin static files are served by Django itself (see django_project/urls.py)
RUN python manage.py collectstatic --noinput \
    && useradd --uid 1000 --create-home app

USER app
EXPOSE 8000
# No access log: every chat completion writes its own metrics line
CMD ["sh", "-c", "python manage.py migrate --noinput && exec uvicorn django_project.asgi:application --host 0.0.0.0 --port \"$PORT\" --workers \"$WEB_CONCURRENCY\" --no-access-log --proxy-headers --forwarded-allow-ips 127.0.0.1 --timeout-keep-alive 75"]
