.PHONY: help install run dev up down build logs test lint format clean db-init db-reset sync-registry

help:
	@echo "MCP Hub Development Commands"
	@echo "============================"
	@echo "make install        Install dependencies (pip install -e .[dev])"
	@echo "make run            Run the API locally with uvicorn (needs postgres/redis reachable)"
	@echo "make dev            Start the full stack via Docker Compose (postgres, redis, backend)"
	@echo "make up             Alias for 'make dev'"
	@echo "make down           Stop the Docker Compose stack"
	@echo "make build          Build the backend Docker image"
	@echo "make logs           Tail logs from the Docker Compose stack"
	@echo "make test           Run tests with coverage"
	@echo "make lint           Run ruff"
	@echo "make format         Format code with black"
	@echo "make clean          Remove caches, coverage output, and build artifacts"
	@echo "make db-init        Create database tables"
	@echo "make db-reset       Recreate the postgres volume, then re-init tables"
	@echo "make sync-registry  Trigger POST /api/v1/admin/sync-registry (needs ADMIN_API_KEY in .env)"

install:
	pip install -e ".[dev]"

run:
	python -m src.main

dev up:
	docker compose up

down:
	docker compose down

build:
	docker compose build backend

logs:
	docker compose logs -f

test:
	pytest tests/ -v --cov=src

lint:
	ruff check src/ tests/

format:
	black src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov dist build

db-init:
	python -c "import asyncio; from src.db.session import init_db; asyncio.run(init_db())"

db-reset:
	docker compose down -v postgres
	docker compose up -d --wait postgres
	$(MAKE) db-init

sync-registry:
	@bash -c 'set -a; [ -f .env ] && source .env; set +a; \
		curl -sS -X POST "http://localhost:$${API_PORT:-8000}/api/v1/admin/sync-registry" \
			-H "X-Admin-Token: $${ADMIN_API_KEY}"; echo'
