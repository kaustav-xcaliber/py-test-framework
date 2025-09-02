.PHONY: help install install-dev test test-cov lint format type-check clean docker-build docker-run docker-stop docker-logs setup-db migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting (flake8)"
	@echo "  format       - Format code (black)"
	@echo "  type-check   - Run type checking (mypy)"
	@echo "  clean        - Clean up cache and temporary files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker Compose services"
	@echo "  docker-logs  - Show Docker Compose logs"
	@echo "  setup-db     - Setup database and run migrations"
	@echo "  migrate      - Run database migrations"
	@echo "  run          - Run the application locally"
	@echo "  run-dev      - Run the application in development mode"

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements.txt
	pip install -e .

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=app --cov-report=html --cov-report=term-missing

# Run linting
lint:
	flake8 app/ tests/

# Format code
format:
	black app/ tests/

# Run type checking
type-check:
	mypy app/

# Clean up cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Build Docker image
docker-build:
	docker build -t api-test-framework:latest .

# Run with Docker Compose
docker-run:
	docker-compose up -d

# Stop Docker Compose services
docker-stop:
	docker-compose down

# Show Docker Compose logs
docker-logs:
	docker-compose logs -f

# Setup database and run migrations
setup-db:
	docker-compose up -d postgres redis
	sleep 10
	alembic upgrade head

# Run database migrations
migrate:
	alembic upgrade head

# Run the application locally
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run the application in development mode
run-dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Check code quality
check: lint format type-check

# Pre-commit checks
pre-commit: check test

# Development setup
dev-setup: install-dev setup-db
	@echo "Development environment setup complete!"
	@echo "Run 'make run-dev' to start the application"

# Production setup
prod-setup: install setup-db
	@echo "Production environment setup complete!"
	@echo "Run 'make run' to start the application"

# Full test suite
test-full: lint format type-check test-cov
	@echo "All checks passed!"

# Docker development
docker-dev: docker-build
	docker-compose -f docker-compose.yml up -d
	@echo "Docker development environment started!"
	@echo "Access the application at http://localhost:8000"
	@echo "Run 'make docker-logs' to view logs"
	@echo "Run 'make docker-stop' to stop services"
