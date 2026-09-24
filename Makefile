-include ~/.yoker/Makefile

.PHONY: env-dev env-run install-pythons test test-cov test-all format format-check lint typecheck check run docs docs-view build pre-publish publish publish-test clean clean-all local-schema web help

## Environment

env-dev: ## Install all dependencies (dev + docs + web)
	uv sync --all-extras

env-run: ## Install runtime dependencies only
	uv sync

install-pythons: ## Install Python 3.10, 3.11, 3.12, 3.13
	uv python install 3.10 3.11 3.12 3.13

## Testing

test: env-dev ## Run tests (usage: make test / optional: TEST=file|file:test_name)
	uv run pytest -v $(TEST)

test-cov: env-dev ## Run tests with coverage
	uv run pytest --cov=schema_tools --cov-report=term-missing $(TEST)

test-all: env-dev ## Run tests on all Python versions
	uv run tox

## Code Quality

format: env-dev ## Format code and fix linting issues
	uv run ruff format src tests
	uv run ruff check --fix src tests

format-check: env-dev ## Check code formatting without modifying
	uv run ruff format --check src tests

lint: env-dev ## Check code for linting issues
	uv run ruff check src tests

typecheck: env-dev ## Run type checking
	uv run mypy src

check: format-check lint typecheck test ## Run all quality checks

## Running

run: env-run ## Run the CLI
	uv run python -m schema_tools

## Documentation

docs: env-dev ## Build HTML documentation
	cd docs && uv run sphinx-build -M html . _build

docs-view: docs ## Build and open documentation in browser
	open docs/_build/html/index.html

## Build & Publish

build: ## Build distribution packages
	uv build

pre-publish: check ## Pre-publication checks (run before publishing)
	@echo "Checking for relative image paths in README..."
	@grep -n '!\[.*](media/' README.md && (echo "ERROR: Relative image paths found - use raw GitHub URLs for PyPI"; exit 1) || echo "OK: No relative image paths"
	@echo "Checking version sync..."
	@VERSION_PY=$$(grep '^version =' pyproject.toml | cut -d'"' -f2); \
	VERSION_INIT=$$(grep '^__version__ = ' src/schema_tools/__init__.py | cut -d'"' -f2); \
	if [ "$$VERSION_PY" != "$$VERSION_INIT" ]; then \
		echo "ERROR: Version mismatch - pyproject.toml ($$VERSION_PY) vs __init__.py ($$VERSION_INIT)"; \
		exit 1; \
	fi; \
	echo "OK: Versions match ($$VERSION_PY)"
	@echo "Pre-publication checks passed"

publish: clean build ## Publish to PyPI (runs pre-publish checks)
	@$(MAKE) pre-publish
	uv run twine upload dist/*

publish-test: build ## Publish to TestPyPI
	uv run twine upload --repository testpypi dist/*

## Cleanup

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .coverage .mypy_cache .ruff_cache
	rm -rf docs/_build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

clean-all: clean ## Remove virtualenv and lock file
	rm -rf .venv uv.lock

# Project-specific targets (preserved from previous Makefile setup)

local-schema: ## Download UBL and PEPPOL schemas into local/schema
	mkdir -p local/schema
	cd local/schema
	curl -O https://docs.oasis-open.org/ubl/os-UBL-2.1/UBL-2.1.zip
	unzip UBL-2.1.zip
	curl -O https://docs.peppol.eu/poacc/billing/3.0/files/PEPPOL-EN16931-UBL.sch
	curl -O https://docs.peppol.eu/poacc/billing/3.0/files/CEN-EN16931-UBL.sch

web: env-run ## Run the schema viewer web app
	uv run gunicorn -k eventlet -w 1 schema_tools.web:app