"""Admin-only write endpoints for compatibility and test-result records.

Nothing in this codebase runs an MCP server to produce these results - they're
recorded here after being produced externally, the same way registry_scraper.py
records externally-produced registry data rather than generating it.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import CompatibilityCreate, CompatibilityRead, TestResultCreate, TestResultRead
from src.api.servers import require_admin
from src.db.models import Compatibility, MCPServer, TestResult, utcnow
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["benchmarks"])


async def _get_server_or_404(namespace: str, db: AsyncSession) -> MCPServer:
    result = await db.execute(select(MCPServer).where(MCPServer.namespace == namespace))
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.post(
    "/servers/{namespace:path}/compatibility",
    response_model=CompatibilityRead,
    dependencies=[Depends(require_admin)],
)
async def record_compatibility(
    namespace: str,
    body: CompatibilityCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        server = await _get_server_or_404(namespace, db)
        tested_at = utcnow()
        stmt = (
            pg_insert(Compatibility)
            .values(
                mcp_server_id=server.id,
                client=body.client,
                compatible=body.compatible,
                tested_at=tested_at,
            )
            .on_conflict_do_update(
                index_elements=["mcp_server_id", "client"],
                set_={"compatible": body.compatible, "tested_at": tested_at},
            )
        )
        await db.execute(stmt)
        await db.commit()
        result = await db.execute(
            select(Compatibility).where(
                Compatibility.mcp_server_id == server.id, Compatibility.client == body.client
            )
        )
        return result.scalars().first()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error recording compatibility for %s", namespace)
        raise HTTPException(status_code=500, detail="Failed to record compatibility")


@router.post(
    "/servers/{namespace:path}/test-results",
    response_model=TestResultRead,
    dependencies=[Depends(require_admin)],
)
async def record_test_result(
    namespace: str,
    body: TestResultCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        server = await _get_server_or_404(namespace, db)
        test_result = TestResult(mcp_server_id=server.id, **body.model_dump())
        db.add(test_result)
        await db.commit()
        await db.refresh(test_result)
        return test_result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error recording test result for %s", namespace)
        raise HTTPException(status_code=500, detail="Failed to record test result")
