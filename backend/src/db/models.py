from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint
from datetime import datetime, timezone
from typing import Optional, List


def utcnow() -> datetime:
    """Naive UTC timestamp, matching the DB's timestamp-without-timezone columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MCPServerBase(SQLModel):
    namespace: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    repository_url: Optional[str] = None
    author: Optional[str] = None
    official_registry_id: Optional[str] = None
    version: Optional[str] = "latest"
    docker_image: Optional[str] = None


class MCPServer(MCPServerBase, table=True):
    __tablename__ = "mcp_servers"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    compatibilities: List["Compatibility"] = Relationship(back_populates="mcp_server")
    test_results: List["TestResult"] = Relationship(back_populates="mcp_server")
    ratings: List["Rating"] = Relationship(back_populates="mcp_server")
    reviews: List["Review"] = Relationship(back_populates="mcp_server")


class CompatibilityBase(SQLModel):
    client: str  # "claude", "cursor", "vscode"
    compatible: bool


class Compatibility(CompatibilityBase, table=True):
    __tablename__ = "compatibilities"
    __table_args__ = (
        UniqueConstraint("mcp_server_id", "client", name="uq_compatibility_server_client"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    mcp_server_id: int = Field(foreign_key="mcp_servers.id")
    tested_at: datetime = Field(default_factory=utcnow)

    mcp_server: MCPServer = Relationship(back_populates="compatibilities")


class TestResultBase(SQLModel):
    version: str
    speed_ms: float  # average, not last-run
    memory_mb: float
    success_rate: float  # fraction of tools that work, 0-1
    error_count: int


class TestResult(TestResultBase, table=True):
    __tablename__ = "test_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    mcp_server_id: int = Field(foreign_key="mcp_servers.id")
    tested_at: datetime = Field(default_factory=utcnow)

    mcp_server: MCPServer = Relationship(back_populates="test_results")


class UserBase(SQLModel):
    github_id: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    avatar_url: Optional[str] = None


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)

    ratings: List["Rating"] = Relationship(back_populates="user")
    reviews: List["Review"] = Relationship(back_populates="user")


class RatingBase(SQLModel):
    score: int = Field(ge=1, le=5)


class Rating(RatingBase, table=True):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("mcp_server_id", "user_id", name="uq_ratings_server_user"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    mcp_server_id: int = Field(foreign_key="mcp_servers.id")
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=utcnow)

    mcp_server: MCPServer = Relationship(back_populates="ratings")
    user: User = Relationship(back_populates="ratings")


class ReviewBase(SQLModel):
    title: str
    content: str
    helpful_count: int = 0


class Review(ReviewBase, table=True):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("mcp_server_id", "user_id", name="uq_reviews_server_user"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    mcp_server_id: int = Field(foreign_key="mcp_servers.id")
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    mcp_server: MCPServer = Relationship(back_populates="reviews")
    user: User = Relationship(back_populates="reviews")
