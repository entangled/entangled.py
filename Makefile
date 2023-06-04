.PHONY: test

test:
	poetry run coverage run --source=entangled -m pytest
	poetry run coverage xml
	poetry run coverage report

docs:
	poetry run mkdocs build
