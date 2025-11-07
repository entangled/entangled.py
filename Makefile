.PHONY: test

test:
	uv run coverage run --source=entangled -m pytest
	uv run coverage xml
	uv run coverage report
	uv run mypy

docs:
	uv run mkdocs build

define test_template =
.PHONY: test-$(1)

test-$(1):
	uv run pytest test/$(1) --cov=entangled/$(1)
	uv run coverage xml
endef

modules = readers io iterators model interface

$(foreach mod,$(modules),$(eval $(call test_template,$(mod))))

.PHONY: test-modules

test-modules:
	uv run pytest $(modules:%=test/%) --cov=entangled -x

