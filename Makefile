# FinOps-Teste Makefile
# Comprehensive development and deployment automation

.PHONY: help install dev build test lint format clean docker-build docker-up docker-down deploy-staging deploy-prod

# Default target
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
RESET := \033[0m

# Project variables
PROJECT_NAME := finops-teste
BACKEND_DIR := backend
FRONTEND_DIR := frontend
DOCKER_COMPOSE_FILE := docker-compose.yml
PYTHON_VERSION := 3.12
NODE_VERSION := 20

help: ## Show this help message
	@echo "$(CYAN)FinOps-Teste Development Commands$(RESET)"
	@echo "=================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(RESET)"
	@echo "  make install     # Install all dependencies"
	@echo "  make dev         # Start development environment"
	@echo "  make test        # Run all tests"
	@echo "  make docker-up   # Start with Docker Compose"

# Installation targets
install: install-backend install-frontend ## Install all dependencies
	@echo "$(GREEN)✓ All dependencies installed$(RESET)"

install-backend: ## Install backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(RESET)"
	@cd $(BACKEND_DIR) && pip install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(RESET)"

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	@cd $(FRONTEND_DIR) && npm install -g pnpm@8.10.0 && pnpm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(RESET)"

# Development targets
dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(RESET)"
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend development server
	@echo "$(BLUE)Starting backend development server...$(RESET)"
	@cd $(BACKEND_DIR) && \
		export PYTHONPATH=. && \
		export ENVIRONMENT=development && \
		export DEBUG=true && \
		export ENABLE_TRACING=false && \
		python cmd/main.py

dev-frontend: ## Start frontend development server
	@echo "$(BLUE)Starting frontend development server...$(RESET)"
	@cd $(FRONTEND_DIR) && pnpm dev

# Build targets
build: build-backend build-frontend ## Build all components
	@echo "$(GREEN)✓ All components built$(RESET)"

build-backend: ## Build backend
	@echo "$(BLUE)Building backend...$(RESET)"
	@cd $(BACKEND_DIR) && python -m py_compile cmd/main.py
	@echo "$(GREEN)✓ Backend built$(RESET)"

build-frontend: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(RESET)"
	@cd $(FRONTEND_DIR) && pnpm build
	@echo "$(GREEN)✓ Frontend built$(RESET)"

# Testing targets
test: test-backend test-frontend ## Run all tests
	@echo "$(GREEN)✓ All tests completed$(RESET)"

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(RESET)"
	@cd $(BACKEND_DIR) && \
		export PYTHONPATH=. && \
		export ENVIRONMENT=testing && \
		python -m pytest tests/ -v --cov=internal --cov-report=term-missing
	@echo "$(GREEN)✓ Backend tests completed$(RESET)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(RESET)"
	@cd $(FRONTEND_DIR) && pnpm test
	@echo "$(GREEN)✓ Frontend tests completed$(RESET)"

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running E2E tests...$(RESET)"
	@cd $(FRONTEND_DIR) && pnpm e2e
	@echo "$(GREEN)✓ E2E tests completed$(RESET)"

test-coverage: ## Generate test coverage reports
	@echo "$(BLUE)Generating coverage reports...$(RESET)"
	@cd $(BACKEND_DIR) && python -m pytest tests/ --cov=internal --cov-report=html --cov-report=xml
	@cd $(FRONTEND_DIR) && pnpm test --coverage
	@echo "$(GREEN)✓ Coverage reports generated$(RESET)"

# Code quality targets
lint: lint-backend lint-frontend ## Run all linters
	@echo "$(GREEN)✓ All linting completed$(RESET)"

lint-backend: ## Run backend linting
	@echo "$(BLUE)Running backend linting...$(RESET)"
	@cd $(BACKEND_DIR) && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@cd $(BACKEND_DIR) && mypy . --ignore-missing-imports
	@cd $(BACKEND_DIR) && bandit -r . -f json -o bandit-report.json || true
	@echo "$(GREEN)✓ Backend linting completed$(RESET)"

lint-frontend: ## Run frontend linting
	@echo "$(BLUE)Running frontend linting...$(RESET)"
	@cd $(FRONTEND_DIR) && pnpm lint
	@cd $(FRONTEND_DIR) && pnpm type-check
	@echo "$(GREEN)✓ Frontend linting completed$(RESET)"

format: format-backend format-frontend ## Format all code
	@echo "$(GREEN)✓ All code formatted$(RESET)"

format-backend: ## Format backend code
	@echo "$(BLUE)Formatting backend code...$(RESET)"
	@cd $(BACKEND_DIR) && black . --line-length 120
	@cd $(BACKEND_DIR) && isort . --profile black
	@echo "$(GREEN)✓ Backend code formatted$(RESET)"

format-frontend: ## Format frontend code
	@echo "$(BLUE)Formatting frontend code...$(RESET)"
	@cd $(FRONTEND_DIR) && pnpm format
	@echo "$(GREEN)✓ Frontend code formatted$(RESET)"

# Database targets
db-setup: ## Set up database
	@echo "$(BLUE)Setting up database...$(RESET)"
	@docker run --name finops-postgres-setup \
		-e POSTGRES_PASSWORD=finops_password \
		-e POSTGRES_DB=finops \
		-e POSTGRES_USER=finops_user \
		-p 5432:5432 -d postgres:15
	@sleep 10
	@docker exec -i finops-postgres-setup psql -U finops_user -d finops < scripts/init-db.sql
	@echo "$(GREEN)✓ Database set up$(RESET)"

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(RESET)"
	@cd $(BACKEND_DIR) && python scripts/migrate.py
	@echo "$(GREEN)✓ Database migrations completed$(RESET)"

db-seed: ## Seed database with sample data
	@echo "$(BLUE)Seeding database...$(RESET)"
	@cd $(BACKEND_DIR) && python scripts/seed.py
	@echo "$(GREEN)✓ Database seeded$(RESET)"

db-reset: ## Reset database
	@echo "$(YELLOW)Resetting database...$(RESET)"
	@docker stop finops-postgres-setup || true
	@docker rm finops-postgres-setup || true
	@make db-setup
	@echo "$(GREEN)✓ Database reset$(RESET)"

# Docker targets
docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(RESET)"
	@docker-compose build
	@echo "$(GREEN)✓ Docker images built$(RESET)"

docker-up: ## Start services with Docker Compose
	@echo "$(BLUE)Starting services with Docker Compose...$(RESET)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started$(RESET)"
	@echo "$(CYAN)Backend API: http://localhost:8000$(RESET)"
	@echo "$(CYAN)Frontend: http://localhost:3000$(RESET)"
	@echo "$(CYAN)Grafana: http://localhost:3001$(RESET)"
	@echo "$(CYAN)Prometheus: http://localhost:9090$(RESET)"

docker-down: ## Stop Docker Compose services
	@echo "$(YELLOW)Stopping Docker Compose services...$(RESET)"
	@docker-compose down
	@echo "$(GREEN)✓ Services stopped$(RESET)"

docker-logs: ## Show Docker Compose logs
	@docker-compose logs -f

docker-clean: ## Clean Docker resources
	@echo "$(YELLOW)Cleaning Docker resources...$(RESET)"
	@docker-compose down -v --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✓ Docker resources cleaned$(RESET)"

# Monitoring targets
monitoring-up: ## Start monitoring stack
	@echo "$(BLUE)Starting monitoring stack...$(RESET)"
	@docker-compose --profile monitoring up -d
	@echo "$(GREEN)✓ Monitoring stack started$(RESET)"
	@echo "$(CYAN)Grafana: http://localhost:3001 (admin/admin123)$(RESET)"
	@echo "$(CYAN)Prometheus: http://localhost:9090$(RESET)"
	@echo "$(CYAN)Jaeger: http://localhost:16686$(RESET)"

monitoring-down: ## Stop monitoring stack
	@echo "$(YELLOW)Stopping monitoring stack...$(RESET)"
	@docker-compose --profile monitoring down
	@echo "$(GREEN)✓ Monitoring stack stopped$(RESET)"

# Deployment targets
deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(RESET)"
	@echo "$(YELLOW)Staging deployment not implemented yet$(RESET)"

deploy-prod: ## Deploy to production environment
	@echo "$(BLUE)Deploying to production...$(RESET)"
	@echo "$(YELLOW)Production deployment not implemented yet$(RESET)"

# Utility targets
clean: ## Clean build artifacts and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -delete
	@find . -type d -name ".mypy_cache" -delete
	@rm -rf $(BACKEND_DIR)/htmlcov/
	@rm -rf $(BACKEND_DIR)/.coverage
	@rm -rf $(FRONTEND_DIR)/dist/
	@rm -rf $(FRONTEND_DIR)/coverage/
	@rm -rf $(FRONTEND_DIR)/node_modules/.cache/
	@echo "$(GREEN)✓ Build artifacts cleaned$(RESET)"

check-deps: ## Check for dependency updates
	@echo "$(BLUE)Checking for dependency updates...$(RESET)"
	@cd $(BACKEND_DIR) && pip list --outdated
	@cd $(FRONTEND_DIR) && pnpm outdated
	@echo "$(GREEN)✓ Dependency check completed$(RESET)"

security-scan: ## Run security scans
	@echo "$(BLUE)Running security scans...$(RESET)"
	@cd $(BACKEND_DIR) && bandit -r . -f json -o bandit-report.json
	@cd $(FRONTEND_DIR) && pnpm audit
	@echo "$(GREEN)✓ Security scans completed$(RESET)"

health-check: ## Check service health
	@echo "$(BLUE)Checking service health...$(RESET)"
	@curl -f http://localhost:8000/health || echo "$(RED)Backend health check failed$(RESET)"
	@curl -f http://localhost:3000/health || echo "$(RED)Frontend health check failed$(RESET)"
	@echo "$(GREEN)✓ Health checks completed$(RESET)"

# Environment setup
setup-dev: ## Set up development environment
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@echo "$(CYAN)Checking Python version...$(RESET)"
	@python --version | grep -q "$(PYTHON_VERSION)" || (echo "$(RED)Python $(PYTHON_VERSION) required$(RESET)" && exit 1)
	@echo "$(CYAN)Checking Node.js version...$(RESET)"
	@node --version | grep -q "v$(NODE_VERSION)" || (echo "$(RED)Node.js $(NODE_VERSION) required$(RESET)" && exit 1)
	@make install
	@cp .env.example .env || echo "$(YELLOW).env file already exists$(RESET)"
	@echo "$(GREEN)✓ Development environment set up$(RESET)"
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  1. Edit .env file with your configuration"
	@echo "  2. Run 'make db-setup' to set up the database"
	@echo "  3. Run 'make dev' to start development servers"

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	@cd $(BACKEND_DIR) && python -m sphinx.cmd.build -b html docs/ docs/_build/html/
	@echo "$(GREEN)✓ Documentation generated$(RESET)"

# Performance testing
perf-test: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(RESET)"
	@echo "$(YELLOW)Performance tests not implemented yet$(RESET)"

# Load testing
load-test: ## Run load tests
	@echo "$(BLUE)Running load tests...$(RESET)"
	@echo "$(YELLOW)Load tests not implemented yet$(RESET)"

# Backup
backup: ## Backup database and important files
	@echo "$(BLUE)Creating backup...$(RESET)"
	@mkdir -p backups
	@docker exec finops-postgres pg_dump -U finops_user finops > backups/db-backup-$(shell date +%Y%m%d-%H%M%S).sql
	@echo "$(GREEN)✓ Backup created$(RESET)"

# Restore
restore: ## Restore database from backup (usage: make restore BACKUP_FILE=filename)
	@echo "$(BLUE)Restoring from backup...$(RESET)"
	@test -n "$(BACKUP_FILE)" || (echo "$(RED)Usage: make restore BACKUP_FILE=filename$(RESET)" && exit 1)
	@docker exec -i finops-postgres psql -U finops_user -d finops < $(BACKUP_FILE)
	@echo "$(GREEN)✓ Database restored$(RESET)"

# Version management
version: ## Show current version
	@echo "$(CYAN)Current version: $(shell cat VERSION 2>/dev/null || echo 'unknown')$(RESET)"

bump-version: ## Bump version (usage: make bump-version TYPE=patch|minor|major)
	@test -n "$(TYPE)" || (echo "$(RED)Usage: make bump-version TYPE=patch|minor|major$(RESET)" && exit 1)
	@echo "$(BLUE)Bumping $(TYPE) version...$(RESET)"
	@echo "$(YELLOW)Version bumping not implemented yet$(RESET)"

# All-in-one targets
full-test: lint test test-e2e security-scan ## Run complete test suite
	@echo "$(GREEN)✓ Full test suite completed$(RESET)"

ci: install lint test build ## Run CI pipeline locally
	@echo "$(GREEN)✓ CI pipeline completed$(RESET)"

# Quick start
quick-start: setup-dev db-setup ## Quick start for new developers
	@echo "$(GREEN)✓ Quick start completed$(RESET)"
	@echo "$(CYAN)Run 'make dev' to start development servers$(RESET)"