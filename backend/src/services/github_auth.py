from datetime import timedelta
from urllib.parse import urlencode
import logging

import httpx2
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import User, utcnow

logger = logging.getLogger(__name__)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

JWT_EXPIRE_DAYS = 30


class GitHubAuthError(Exception):
    """Raised when the OAuth handshake or JWT verification fails."""


class GitHubAuthService:
    def build_authorize_url(self, state: str) -> str:
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "read:user",
            "state": state,
        }
        return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> str:
        async with httpx2.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                GITHUB_TOKEN_URL,
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": settings.github_redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        access_token = data.get("access_token")
        if not access_token:
            raise GitHubAuthError(
                data.get("error_description") or "GitHub did not return an access token"
            )
        return access_token

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx2.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_or_create_user(self, github_user: dict, db: AsyncSession) -> User:
        github_id = str(github_user["id"])
        result = await db.execute(select(User).where(User.github_id == github_id))
        user = result.scalars().first()

        if user:
            user.username = github_user.get("login", user.username)
            user.avatar_url = github_user.get("avatar_url")
        else:
            user = User(
                github_id=github_id,
                username=github_user["login"],
                avatar_url=github_user.get("avatar_url"),
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)
        return user

    def mint_jwt(self, user: User) -> str:
        payload = {"sub": str(user.id), "exp": utcnow() + timedelta(days=JWT_EXPIRE_DAYS)}
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def decode_jwt(self, token: str) -> int:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except JWTError as exc:
            raise GitHubAuthError("Invalid or expired session") from exc
        return int(payload["sub"])
