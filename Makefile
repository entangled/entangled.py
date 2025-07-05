.PHONY: test

test:
	hatch run coverage run --source=entangled -m pytest
	hatch run coverage xml
	hatch run coverage report
	hatch run mypy

docs:
	hatch run mkdocs build
