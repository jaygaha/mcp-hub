# MCP Hub

A discovery platform for MCP (Model Context Protocol) servers. It syncs from the official registry into Postgres and exposes a search/browse API over that data.

This is early. The backend and registry sync work end to end, but ratings, reviews, compatibility testing, benchmarks and the frontend are only modeled in the database so far. No API or UI for those yet.

## Stack

- FastAPI, SQLModel/SQLAlchemy (async), Postgres via asyncpg
- Redis and Celery are dependencies and Redis runs in Compose, but nothing in the code uses either yet
- Docker Compose for Postgres, Redis, and the backend locally

## Setup

```bash
cp .env.example .env
docker compose up
```

API docs: `http://localhost:8000/docs` (or whatever port you set `API_PORT` to in `.env`).

A `Makefile` wraps the common commands. Run `make help` for the full list (`dev`, `test`, `lint`, `db-reset`, `sync-registry`, ...).

### Running the backend without Docker

Needs Python 3.14+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

docker compose up -d postgres redis
make db-init
python -m src.main
```

## Syncing the registry

```bash
make sync-registry
```

This walks every page of the official registry and upserts each server into Postgres, keeping only the latest version when the registry lists more than one. It retries on timeouts and 429s (honoring `Retry-After`), and paces requests to avoid the registry's rate limit. Against the real registry that's currently ~16,700 servers, so a full sync takes fifteen to twenty minutes, mostly waiting on Postgres round trips (see TODO.md).

It's admin-only: `.env.example` ships a placeholder `ADMIN_API_KEY`, sent back as an `X-Admin-Token` header via `make sync-registry`. Change it before running this anywhere that isn't your own machine. With no key configured at all, the endpoint refuses everyone with a 503 rather than staying open.

## Tests

```bash
docker compose up -d postgres redis
make test
```

Tests run against those same containers, but not against your dev data. `tests/conftest.py` points `DATABASE_URL` at a separate `<db>_test` database (created automatically on first run) and resets its tables before and after every test, so order doesn't matter and your dev database - including anything pulled in via `make sync-registry` - is never touched.

## Not built yet

- Frontend
- Ratings, reviews, compatibility, and benchmark endpoints (the tables exist, nothing serves them)
- Any auth beyond the admin token on the sync endpoint
