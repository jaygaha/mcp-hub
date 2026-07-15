import asyncio

from tests._test_env import (
    TEST_DATABASE_URL,
)  # noqa: E402 - must run before any src import

import asyncpg
import pytest
from sqlalchemy import delete

from src.db.models import Compatibility, MCPServer, Rating, Review, TestResult, User
from src.db.session import AsyncSessionLocal, engine, init_db

_MODELS_IN_FK_ORDER = (Review, Rating, Compatibility, TestResult, MCPServer, User)


async def _ensure_test_database_exists():
    # CREATE DATABASE can't run inside a transaction; connecting straight to
    # the "postgres" maintenance database sidesteps that.
    db_name = TEST_DATABASE_URL.rsplit("/", 1)[-1]
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    conn = await asyncpg.connect(admin_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


async def _reset_tables():
    # Drops any connection left bound to a previous test's closed event loop -
    # asyncpg connections are loop-bound, and tests mix pytest-asyncio's loop
    # with TestClient's own anyio portal loop against one shared engine.
    await engine.dispose()
    await init_db()
    async with AsyncSessionLocal() as session:
        for model in _MODELS_IN_FK_ORDER:
            await session.execute(delete(model))
        await session.commit()
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Runs once per test session: creates the dedicated test database if
    it doesn't exist yet."""
    asyncio.run(_ensure_test_database_exists())


@pytest.fixture(autouse=True)
def clean_database(_test_database):
    """Every test starts and ends against empty tables in the dedicated
    test database - dev data (including anything synced via
    make sync-registry) is never touched."""
    asyncio.run(_reset_tables())
    yield
    asyncio.run(_reset_tables())
