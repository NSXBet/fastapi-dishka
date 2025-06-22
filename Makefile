.PHONY: all
all: setup test-unit test-examples lint format

# Default help command
.PHONY: help
help:
	@echo "FastAPI + Dishka Development Commands"
	@echo "=========================="
	@echo "install        - Install the package"
	@echo "install-dev    - Install the package in development mode"
	@echo "setup          - Setup development environment"
	@echo "test           - Run tests"
	@echo "lint           - Run linting (flake8, mypy)"
	@echo "format         - Format code (black, isort)"
	@echo "clean          - Clean build artifacts"

# Installation commands
.PHONY: install
install:
	pip install -e .[dev]

# Testing commands
.PHONY: test test-unit test-examples test-cov
test: test-unit test-examples

test-unit unit:
	pytest --ignore=tests/test_examples_script.py

test-unit-html html:
	pytest --cov=fastapi_dishka --cov-report=html --cov-report=term-missing

test-examples:
	pytest examples/docs/06_testing.py

# Code quality commands
lint:
	ruff check src/ tests/ --fix 
	ruff check src/ tests/
	pflake8 --max-line-length 120 src/ tests/
	mypy src/

format:
	black -l 120 src/ tests/
	isort src/ tests/

# Clean and build commands
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development setup
setup: install
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."