.PHONY: help install run dev up down build logs test lint format clean db-init db-reset sync-registry \
	frontend-install frontend-dev frontend-build frontend-lint frontend-format

help:
	@echo "MCP Hub Development Commands"
	@echo "============================"
	@echo "make install          Install backend dependencies (pip install -e .[dev])"
	@echo "make run              Run the API locally with uvicorn (needs postgres/redis reachable)"
	@echo "make dev              Start the full stack via Docker Compose (postgres, redis, backend, frontend)"
	@echo "make up               Alias for 'make dev'"
	@echo "make down             Stop the Docker Compose stack"
	@echo "make build            Build the backend Docker image"
	@echo "make logs             Tail logs from the Docker Compose stack"
	@echo "make test             Run backend tests with coverage"
	@echo "make lint             Run ruff"
	@echo "make format           Format code with black"
	@echo "make clean            Remove caches, coverage output, and build artifacts"
	@echo "make db-init          Create database tables"
	@echo "make db-reset         Recreate the postgres volume, then re-init tables"
	@echo "make sync-registry    Trigger POST /api/v1/admin/sync-registry (needs ADMIN_API_KEY in .env)"
	@echo "make frontend-install Install frontend dependencies (npm install)"
	@echo "make frontend-dev     Run the frontend locally with npm (needs the backend reachable)"
	@echo "make frontend-build   Build the frontend Docker image"
	@echo "make frontend-lint    Run eslint on the frontend"
	@echo "make frontend-format  Format the frontend with prettier"

install:
	cd backend && pip install -e ".[dev]"

run:
	cd backend && python -m src.main

dev up:
	docker compose up

down:
	docker compose down

build:
	docker compose build backend

logs:
	docker compose logs -f

test:
	cd backend && pytest tests/ -v --cov=src

lint:
	cd backend && ruff check src/ tests/

format:
	cd backend && black src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf backend/.pytest_cache backend/.coverage backend/htmlcov backend/dist backend/build

db-init:
	cd backend && python -c "import asyncio; from src.db.session import init_db; asyncio.run(init_db())"

db-reset:
	docker compose down -v postgres
	docker compose up -d --wait postgres
	$(MAKE) db-init

sync-registry:
	@bash -c 'set -a; [ -f .env ] && source .env; set +a; \
		curl -sS -X POST "http://localhost:$${API_PORT:-8000}/api/v1/admin/sync-registry" \
			-H "X-Admin-Token: $${ADMIN_API_KEY}"; echo'

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	docker compose build frontend

frontend-lint:
	cd frontend && npm run lint

frontend-format:
	cd frontend && npm run format
