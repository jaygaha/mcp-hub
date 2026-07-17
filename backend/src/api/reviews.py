from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user, get_current_user_optional
from src.api.schemas import (
    RatingCreate,
    RatingSummaryResponse,
    ReviewCreate,
    ReviewListResponse,
    ReviewRead,
)
from src.db.models import MCPServer, Rating, Review, User, utcnow
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["reviews"])


async def _get_server_or_404(namespace: str, db: AsyncSession) -> MCPServer:
    result = await db.execute(select(MCPServer).where(MCPServer.namespace == namespace))
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


async def _rating_summary(
    server_id: int, my_score: Optional[int], db: AsyncSession
) -> RatingSummaryResponse:
    average = (
        await db.execute(select(func.avg(Rating.score)).where(Rating.mcp_server_id == server_id))
    ).scalar()
    total = (
        await db.execute(
            select(func.count(Rating.id)).where(Rating.mcp_server_id == server_id)
        )
    ).scalar() or 0
    counts = dict(
        (
            await db.execute(
                select(Rating.score, func.count(Rating.id))
                .where(Rating.mcp_server_id == server_id)
                .group_by(Rating.score)
            )
        ).all()
    )
    return {
        "average_score": round(average or 0, 1),
        "total_ratings": total,
        "distribution": [
            {"score": score, "count": counts.get(score, 0)} for score in (5, 4, 3, 2, 1)
        ],
        "my_score": my_score,
    }


@router.post("/servers/{namespace:path}/ratings", response_model=RatingSummaryResponse)
async def rate_server(
    namespace: str,
    body: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        server = await _get_server_or_404(namespace, db)
        stmt = (
            pg_insert(Rating)
            .values(mcp_server_id=server.id, user_id=current_user.id, score=body.score)
            .on_conflict_do_update(
                index_elements=["mcp_server_id", "user_id"],
                set_={"score": body.score},
            )
        )
        await db.execute(stmt)
        await db.commit()
        return await _rating_summary(server.id, body.score, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error rating server %s", namespace)
        raise HTTPException(status_code=500, detail="Failed to submit rating")


@router.get("/servers/{namespace:path}/ratings", response_model=RatingSummaryResponse)
async def get_ratings(
    namespace: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    try:
        server = await _get_server_or_404(namespace, db)
        my_score = None
        if current_user:
            my_score = (
                await db.execute(
                    select(Rating.score).where(
                        Rating.mcp_server_id == server.id, Rating.user_id == current_user.id
                    )
                )
            ).scalar()
        return await _rating_summary(server.id, my_score, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching ratings for %s", namespace)
        raise HTTPException(status_code=500, detail="Failed to fetch ratings")


def _review_read(review: Review, username: str, avatar_url: Optional[str]) -> dict:
    return {
        **review.model_dump(),
        "author_username": username,
        "author_avatar_url": avatar_url,
    }


@router.post("/servers/{namespace:path}/reviews", response_model=ReviewRead)
async def submit_review(
    namespace: str,
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        server = await _get_server_or_404(namespace, db)
        existing = (
            await db.execute(
                select(Review).where(
                    Review.mcp_server_id == server.id, Review.user_id == current_user.id
                )
            )
        ).scalars().first()

        if existing:
            existing.title = body.title
            existing.content = body.content
            existing.updated_at = utcnow()
            review = existing
        else:
            created_at = utcnow()
            review = Review(
                mcp_server_id=server.id,
                user_id=current_user.id,
                title=body.title,
                content=body.content,
                created_at=created_at,
                updated_at=created_at,
            )
            db.add(review)

        await db.commit()
        await db.refresh(review)
        return _review_read(review, current_user.username, current_user.avatar_url)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error submitting review for %s", namespace)
        raise HTTPException(status_code=500, detail="Failed to submit review")


@router.get("/servers/{namespace:path}/reviews", response_model=ReviewListResponse)
async def list_reviews(
    namespace: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    try:
        server = await _get_server_or_404(namespace, db)
        rows = (
            await db.execute(
                select(Review, User.username, User.avatar_url)
                .join(User, Review.user_id == User.id)
                .where(Review.mcp_server_id == server.id)
                .order_by(Review.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
        ).all()
        total = (
            await db.execute(
                select(func.count(Review.id)).where(Review.mcp_server_id == server.id)
            )
        ).scalar() or 0
        return {
            "status": "success",
            "data": [_review_read(review, username, avatar_url) for review, username, avatar_url in rows],
            "pagination": {"skip": skip, "limit": limit, "total": total},
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching reviews for %s", namespace)
        raise HTTPException(status_code=500, detail="Failed to fetch reviews")


@router.get("/servers/{namespace:path}/reviews/me", response_model=ReviewRead)
async def get_my_review(
    namespace: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        server = await _get_server_or_404(namespace, db)
        review = (
            await db.execute(
                select(Review).where(
                    Review.mcp_server_id == server.id, Review.user_id == current_user.id
                )
            )
        ).scalars().first()
        if not review:
            raise HTTPException(status_code=404, detail="You haven't reviewed this server yet")
        return _review_read(review, current_user.username, current_user.avatar_url)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching own review for %s", namespace)
        raise HTTPException(status_code=500, detail="Failed to fetch review")
