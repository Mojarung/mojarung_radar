.PHONY: help install up down logs migrate test lint format clean

help:
	@echo "RADAR - Makefile commands"
	@echo ""
	@echo "install       - Install dependencies with uv"
	@echo "up            - Start services with docker-compose"
	@echo "down          - Stop services"
	@echo "logs          - Show logs"
	@echo "migrate       - Run database migrations"
	@echo "migration     - Create new migration"
	@echo "test          - Run tests"
	@echo "lint          - Run linters"
	@echo "format        - Format code"
	@echo "clean         - Clean cache files"

install:
	uv pip install -e .

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f app

migrate:
	alembic upgrade head

migration:
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name"

test:
	pytest -v

lint:
	ruff check src/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

