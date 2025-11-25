.PHONY: help install test lint format type-check security clean coverage pre-commit

help:
	@echo "AWS FinOps Analyzer - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linters (ruff, flake8)"
	@echo "  make format        - Format code (black, isort)"
	@echo "  make type-check    - Run type checking (mypy)"
	@echo "  make security      - Run security checks (bandit)"
	@echo "  make coverage      - Generate coverage report"
	@echo "  make pre-commit    - Install pre-commit hooks"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make all           - Run format, lint, type-check, and test"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint:
	ruff check src/ tests/
	flake8 src/ tests/ --max-line-length=120

format:
	black src/ tests/
	isort src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/

security:
	bandit -r src/ -c pyproject.toml

pre-commit:
	pre-commit install
	pre-commit run --all-files

coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

mutation-test:
	mutmut run --paths-to-mutate=src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

all: format lint type-check test
	@echo "All checks passed!"

ci: lint type-check test-coverage
	@echo "CI pipeline completed!"
