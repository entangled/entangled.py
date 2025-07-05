.PHONY: test

test:
	uv run coverage run --source=entangled -m pytest
	uv run coverage xml
	uv run coverage report
	uv run mypy

docs:
	uv run mkdocs build
