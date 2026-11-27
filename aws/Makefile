install:
	uv sync --all-packages

lint:
	uv run ruff check
	uv run ruff format --check
	cd cdk && uv run mypy app.py stacks

synth:
	cd cdk && cdk synth --quiet
diff:
	cd cdk && cdk diff --all
deploy:
	cd cdk && cdk deploy --all
