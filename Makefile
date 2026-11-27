COMPOSE = docker compose --env-file src/.env -f compose.dev.yml
MANAGE = uv run python src/manage.py

install:
	uv sync --locked
pre-commit.install:
	uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

# Local run without Docker: Postgres from `make db`, the app with reload
db:
	$(COMPOSE) up -d --wait db
run:
	cd src && uv run uvicorn django_project.asgi:application --reload --port 8000

up:
	$(COMPOSE) up -d --build --wait
down:
	$(COMPOSE) down
logs:
	$(COMPOSE) logs -f

migrations:
	$(MANAGE) makemigrations
migrate:
	$(MANAGE) migrate
superuser:
	$(MANAGE) createsuperuser

lint:
	uv run ruff check src/
	uv run ruff format --check src/
	uv run mypy src/
test:
	uv run pytest
