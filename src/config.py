import logging
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_JWT_SECRET = "your-super-secret-jwt-key-change-this"


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/mcp_hub"
    redis_url: str = "redis://localhost:6379"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # No wildcard - allow_credentials=True makes "*" reflect any origin.
    cors_origins: str = "http://localhost:3000"

    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None

    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"

    # Required as an X-Admin-Token header on admin-only routes.
    admin_api_key: Optional[str] = None

    official_registry_url: str = "https://registry.modelcontextprotocol.io/v0.1"
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @model_validator(mode="after")
    def _warn_on_insecure_production_defaults(self) -> "Settings":
        if self.environment != "development":
            if self.jwt_secret == _DEFAULT_JWT_SECRET:
                logger.warning(
                    "JWT_SECRET is still the placeholder default outside of development. "
                    "Set a real secret via the JWT_SECRET env var."
                )
            if not self.admin_api_key:
                logger.warning(
                    "ADMIN_API_KEY is not set outside of development. "
                    "Admin-only endpoints will refuse all requests until it is configured."
                )
        return self


settings = Settings()
