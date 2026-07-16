# MCP Hub

A discovery platform for MCP (Model Context Protocol) servers. It syncs from the official registry into Postgres and exposes a search/browse API and a Next.js UI over that data.

![MCP Hub homepage - search and browse MCP servers, dark mode](ui.png)

This is early. The backend, registry sync, and a read-only frontend (search, browse, server detail) work end to end, but ratings, reviews, compatibility testing, and benchmarks are only modeled in the database so far - no write endpoints or UI for those yet.

## Stack

- Backend: FastAPI, SQLModel/SQLAlchemy (async), Postgres via asyncpg
- Frontend: Next.js (App Router), TypeScript, Tailwind, shadcn/ui
- Redis and Celery are dependencies and Redis runs in Compose, but nothing in the code uses either yet
- Docker Compose for Postgres, Redis, the backend, and the frontend locally

## Setup

```bash
cp .env.example .env
docker compose up
```

Frontend: `http://localhost:3000` (or whatever port you set `FRONTEND_PORT` to). API docs: `http://localhost:8000/docs` (or `API_PORT`).

A `Makefile` wraps the common commands. Run `make help` for the full list (`dev`, `test`, `lint`, `db-reset`, `sync-registry`, `frontend-dev`, ...).

### Running the backend without Docker

Needs Python 3.14+.

```bash
cd backend && python -m venv .venv && source .venv/bin/activate && cd ..

make install
docker compose up -d postgres redis
make db-init
make run
```

### Running the frontend without Docker

Needs Node 22+ and the backend reachable (either via `docker compose up -d backend postgres redis`, or `make run` above).

```bash
cp frontend/.env.example frontend/.env.local
make frontend-install
make frontend-dev
```

The frontend fetches the backend directly from Server Components at request time - there's no API proxy layer, and no client-side code ever calls the backend (nothing in a `"use client"` file imports the data layer). `BACKEND_INTERNAL_URL` is server-only and never reaches the browser. Ratings, test results, and compatibility on the server detail page show honest "not available yet" states, since the backend has no write endpoints for them yet.

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

Tests run against those same containers, but not against your dev data. `backend/tests/conftest.py` points `DATABASE_URL` at a separate `<db>_test` database (created automatically on first run) and resets its tables before and after every test, so order doesn't matter and your dev database - including anything pulled in via `make sync-registry` - is never touched.

The frontend has no test suite yet, just `make frontend-lint` and `cd frontend && npm run build` as a static-correctness gate (type errors, mainly).

## Not built yet

- Ratings, reviews, compatibility, and benchmark endpoints (the tables exist, nothing serves them, and the frontend shows explicit empty states for them)
- Any auth beyond the admin token on the sync endpoint
