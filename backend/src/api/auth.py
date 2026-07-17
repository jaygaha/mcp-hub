import secrets
from typing import Optional
import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import UserRead
from src.config import settings
from src.db.models import User
from src.db.session import get_db
from src.services.github_auth import GitHubAuthError, GitHubAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

ACCESS_TOKEN_COOKIE = "access_token"
STATE_COOKIE = "oauth_state"
_ACCESS_TOKEN_MAX_AGE = 60 * 60 * 24 * 30  # 30 days, matching the JWT's own expiry
_STATE_MAX_AGE = 600  # long enough to complete the GitHub consent screen

auth_service = GitHubAuthService()


def _cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "secure": settings.environment != "development",
        "samesite": "lax",
    }


@router.get("/login")
async def login():
    if not settings.github_client_id:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")

    state = secrets.token_urlsafe(24)
    response = RedirectResponse(auth_service.build_authorize_url(state), status_code=307)
    response.set_cookie(STATE_COOKIE, state, max_age=_STATE_MAX_AGE, **_cookie_kwargs())
    return response


@router.get("/github/callback")
async def github_callback(
    state: str,
    code: Optional[str] = None,
    error: Optional[str] = None,
    oauth_state: Optional[str] = Cookie(default=None, alias=STATE_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    if error or not code:
        return RedirectResponse(f"{settings.frontend_url}?auth_error=denied", status_code=307)

    if not oauth_state or state != oauth_state:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    try:
        access_token = await auth_service.exchange_code_for_token(code)
        github_user = await auth_service.get_user_info(access_token)
        user = await auth_service.get_or_create_user(github_user, db)
        jwt_token = auth_service.mint_jwt(user)
    except GitHubAuthError:
        logger.exception("GitHub OAuth callback failed")
        raise HTTPException(status_code=401, detail="GitHub authentication failed")

    response = RedirectResponse(settings.frontend_url, status_code=307)
    response.delete_cookie(STATE_COOKIE)
    response.set_cookie(
        ACCESS_TOKEN_COOKIE, jwt_token, max_age=_ACCESS_TOKEN_MAX_AGE, **_cookie_kwargs()
    )
    return response


async def get_current_user(
    access_token: Optional[str] = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = auth_service.decode_jwt(access_token)
    except GitHubAuthError:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_current_user_optional(
    access_token: Optional[str] = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not access_token:
        return None
    try:
        return await get_current_user(access_token, db)
    except HTTPException:
        return None


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/logout")
async def logout():
    response = RedirectResponse(settings.frontend_url, status_code=307)
    response.delete_cookie(ACCESS_TOKEN_COOKIE)
    return response
