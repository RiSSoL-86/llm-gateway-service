FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.17 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=django_project.settings \
    PORT=8000
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY src ./

RUN useradd --uid 1000 --create-home app
USER app
CMD ["sh", "-c", "python manage.py migrate --noinput && exec uvicorn django_project.asgi:application --host 0.0.0.0 --port \"$PORT\" --reload --reload-dir /app"]
