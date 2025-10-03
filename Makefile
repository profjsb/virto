# Docker commands
up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

restart:
	docker compose restart api console

# Testing commands
.PHONY: help install test test-backend test-frontend test-all lint format clean dev-backend dev-frontend setup-db

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	uv sync
	cd console && npm install

test-backend: ## Run backend tests
	uv run pytest -v

test-backend-cov: ## Run backend tests with coverage
	uv run pytest -v --cov=src --cov-report=html --cov-report=term

test-frontend: ## Run frontend tests
	cd console && npm run test

test-frontend-cov: ## Run frontend tests with coverage
	cd console && npm run test:coverage

test-all: test-backend test-frontend ## Run all tests

test-integration: ## Run integration tests only
	uv run pytest -v -m integration

test-unit: ## Run unit tests only
	uv run pytest -v -m unit

lint: ## Run linters for backend and frontend
	uv run ruff check src tests
	cd console && npm run lint

lint-fix: ## Run linters with auto-fix
	uv run ruff check --fix src tests
	cd console && npm run lint --fix

format: ## Format code (backend + frontend)
	uv run ruff format src tests

type-check: ## Run type checking
	cd console && npm run type-check

clean: ## Clean build artifacts and caches
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf console/coverage
	rm -rf console/node_modules/.cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev-backend: ## Start backend development server
	uv run uvicorn src.app:app --reload

dev-frontend: ## Start frontend development server
	cd console && npm run dev

setup-db: ## Initialize database with migrations
	uv run alembic upgrade head

reset-db: ## Reset database (drop and recreate)
	uv run alembic downgrade base
	uv run alembic upgrade head

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install

pre-commit-run: ## Run pre-commit on all files
	uv run pre-commit run --all-files

ci: lint test-all ## Run CI checks locally
	@echo "✅ All CI checks passed!"

