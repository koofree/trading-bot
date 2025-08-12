.PHONY: help install lint format test clean

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Installation
install: ## Install all dependencies (backend and frontend)
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	cd backend && pip install -r requirements-dev.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install --legacy-peer-deps
	@echo "Installing pre-commit hooks..."
	pre-commit install

# Backend commands
backend-lint: ## Run Python linters
	@echo "Running Black..."
	cd backend && black . --check
	@echo "Running Ruff..."
	cd backend && ruff check .
	@echo "Running mypy..."
	cd backend && mypy .

backend-format: ## Format Python code
	@echo "Formatting with Black..."
	cd backend && black .
	@echo "Fixing with Ruff..."
	cd backend && ruff check . --fix

backend-test: ## Run backend tests
	cd backend && pytest

# Frontend commands
frontend-lint: ## Run TypeScript/React linters
	@echo "Type checking..."
	cd frontend && npm run type-check
	@echo "Running ESLint..."
	cd frontend && npm run lint
	@echo "Checking Prettier format..."
	cd frontend && npm run format:check

frontend-format: ## Format TypeScript/React code
	@echo "Running ESLint fix..."
	cd frontend && npm run lint:fix
	@echo "Running Prettier..."
	cd frontend && npm run format

frontend-test: ## Run frontend tests
	cd frontend && npm test -- --watchAll=false

# Combined commands
lint: backend-lint frontend-lint ## Run all linters

format: backend-format frontend-format ## Format all code

test: backend-test frontend-test ## Run all tests

validate: ## Validate entire project (lint + type check)
	@echo "Validating backend..."
	$(MAKE) backend-lint
	@echo "Validating frontend..."
	cd frontend && npm run validate

# Development
dev-backend: ## Start backend development server
	cd backend && python -m uvicorn api.main:app --reload --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm start

dev: ## Start both servers in parallel (requires GNU parallel)
	@echo "Starting development servers..."
	@parallel --will-cite ::: "make dev-backend" "make dev-frontend"

# Docker commands
docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

# Utility
clean: ## Clean build artifacts and caches
	@echo "Cleaning Python caches..."
	find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete
	find backend -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaning frontend build..."
	rm -rf frontend/build frontend/dist frontend/.eslintcache
	@echo "Cleaning logs..."
	rm -rf logs/*.log

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

update-deps: ## Update dependencies to latest versions
	@echo "Updating Python dependencies..."
	cd backend && pip-compile --upgrade requirements.in
	cd backend && pip-compile --upgrade requirements-dev.in
	@echo "Updating Node dependencies..."
	cd frontend && npm update

security-check: ## Run security checks
	@echo "Checking Python dependencies..."
	cd backend && pip-audit
	@echo "Checking Node dependencies..."
	cd frontend && npm audit