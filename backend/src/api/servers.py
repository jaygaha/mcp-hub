from datetime import timedelta
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.api.schemas import (
    CompatibilityClient,
    HealthResponse,
    ServerDetailResponse,
    ServerListResponse,
    SyncRegistryResponse,
)
from src.config import settings
from src.db.models import MCPServer, TestResult, Rating, Compatibility, utcnow
from src.db.session import get_db
from src.services.registry_scraper import RegistryScraper
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["servers"])


async def require_admin(x_admin_token: Optional[str] = Header(None)) -> None:
    """Fail closed: admin routes refuse everyone until ADMIN_API_KEY is set."""
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin API is not configured")
    if x_admin_token != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")


@router.get("/servers", response_model=ServerListResponse)
async def list_servers(
    search: Optional[str] = Query(None, description="Search by name or description"),
    sort: str = Query("popular", description="Sort by: popular, newest, trending, rating"),
    min_rating: Optional[float] = Query(None, ge=1, le=5),
    client: Optional[CompatibilityClient] = Query(
        None, description="Only servers marked compatible with this client"
    ),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List MCP servers with search, sort, filtering, and pagination."""
    try:
        search_clause = None
        if search:
            search_term = f"%{search}%"
            search_clause = (
                MCPServer.name.ilike(search_term)
                | MCPServer.description.ilike(search_term)
                | MCPServer.namespace.ilike(search_term)
            )

        avg_rating_expr = (
            select(func.avg(Rating.score))
            .where(Rating.mcp_server_id == MCPServer.id)
            .correlate(MCPServer)
            .scalar_subquery()
        )
        rating_count_expr = (
            select(func.count(Rating.id))
            .where(Rating.mcp_server_id == MCPServer.id)
            .correlate(MCPServer)
            .scalar_subquery()
        )

        query = select(MCPServer, avg_rating_expr, rating_count_expr)
        count_query = select(func.count(MCPServer.id))

        if search_clause is not None:
            query = query.where(search_clause)
            count_query = count_query.where(search_clause)

        if min_rating is not None:
            # A server with no ratings has a NULL average, which fails this
            # comparison in SQL - correctly excluded rather than erroring.
            query = query.where(avg_rating_expr >= min_rating)
            count_query = count_query.where(avg_rating_expr >= min_rating)

        if client is not None:
            compat_exists = (
                select(Compatibility.id)
                .where(
                    Compatibility.mcp_server_id == MCPServer.id,
                    Compatibility.client == client,
                    Compatibility.compatible.is_(True),
                )
                .correlate(MCPServer)
                .exists()
            )
            query = query.where(compat_exists)
            count_query = count_query.where(compat_exists)

        if sort == "newest":
            query = query.order_by(MCPServer.created_at.desc())
        elif sort == "trending":
            recent_cutoff = utcnow() - timedelta(days=7)
            recent_rating_count = (
                select(func.count(Rating.id))
                .where(
                    Rating.mcp_server_id == MCPServer.id,
                    Rating.created_at >= recent_cutoff,
                )
                .correlate(MCPServer)
                .scalar_subquery()
            )
            query = query.order_by(
                recent_rating_count.desc(), MCPServer.updated_at.desc()
            )
        elif sort == "rating":
            # Postgres sorts NULL first in DESC order by default, which would
            # otherwise put every unrated server at the top of this sort.
            query = query.order_by(
                avg_rating_expr.desc().nulls_last(), MCPServer.id.desc()
            )
        else:  # popular
            query = query.order_by(MCPServer.id.desc())

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        count_result = await db.execute(count_query)
        total = count_result.scalar()

        return {
            "status": "success",
            "data": [
                {
                    **server.model_dump(),
                    "average_rating": round(avg_rating or 0, 1),
                    "total_ratings": rating_count or 0,
                }
                for server, avg_rating, rating_count in rows
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
            },
        }

    except Exception:
        logger.exception("Error listing servers")
        raise HTTPException(status_code=500, detail="Failed to list servers")


# :path (not str) - registry namespaces contain "/", e.g. "ac.inference.sh/mcp"
@router.get("/servers/{namespace:path}", response_model=ServerDetailResponse)
async def get_server(
    namespace: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a server's details, recent test results, average rating, and compatibility info."""
    if not namespace:
        raise HTTPException(status_code=404, detail="Server not found")
    try:
        query = select(MCPServer).where(MCPServer.namespace == namespace)
        result = await db.execute(query)
        server = result.scalars().first()

        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        test_query = (
            select(TestResult)
            .where(TestResult.mcp_server_id == server.id)
            .order_by(TestResult.tested_at.desc())
            .limit(5)
        )
        test_result = await db.execute(test_query)
        test_results = test_result.scalars().all()

        rating_query = select(func.avg(Rating.score)).where(
            Rating.mcp_server_id == server.id
        )
        rating_result = await db.execute(rating_query)
        avg_rating = rating_result.scalar() or 0

        compat_query = select(Compatibility).where(
            Compatibility.mcp_server_id == server.id
        )
        compat_result = await db.execute(compat_query)
        compatibilities = compat_result.scalars().all()

        return {
            "status": "success",
            "data": {
                "server": server,
                "test_results": test_results,
                "average_rating": round(avg_rating, 1),
                "compatibilities": compatibilities,
            },
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching server %s", namespace)
        raise HTTPException(status_code=500, detail="Failed to fetch server")


@router.post(
    "/admin/sync-registry",
    response_model=SyncRegistryResponse,
    dependencies=[Depends(require_admin)],
)
async def sync_registry(
    db: AsyncSession = Depends(get_db),
):
    """Sync all MCPs from official registry (admin only, requires X-Admin-Token)"""
    try:
        scraper = RegistryScraper()
        result = await scraper.sync_all_servers(db)
        return result
    except Exception:
        logger.exception("Error triggering registry sync")
        raise HTTPException(status_code=500, detail="Failed to sync registry")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}
