.PHONY: help install dev-install run test lint format clean docker-build docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

dev-install: install ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

run: ## Run the bot locally
	python3 -m src.bot.main

test: ## Run all tests
	pytest

test-unit: ## Run unit tests
	pytest tests/unit/

test-e2e: ## Run e2e tests
	pytest tests/e2e/

test-cov: ## Run tests with coverage
	pytest --cov=src --cov-report=html --cov-report=term

lint: ## Run linters
	flake8 src tests
	mypy src

format: ## Format code with black
	black src tests

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf *.egg-info

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

db-init: ## Initialize database
	python -m src.storage.init_db

db-migrate: ## Run database migrations
	alembic upgrade head

requirements: ## Update requirements files
	pip-compile requirements.in
	pip-compile requirements-dev.in