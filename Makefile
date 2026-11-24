.PHONY: install lint test check fmt

install:
	pip install -e ".[dev,media]"

lint:
	ruff check src tests

fmt:
	ruff format src tests && ruff check --fix src tests

test:
	pytest -q

check: lint test
