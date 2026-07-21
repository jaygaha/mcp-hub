from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ServerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    namespace: str
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    author: Optional[str] = None
    official_registry_id: Optional[str] = None
    version: Optional[str] = None
    docker_image: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaginationInfo(BaseModel):
    skip: int
    limit: int
    total: int


class ServerListResponse(BaseModel):
    status: str
    data: List[ServerRead]
    pagination: PaginationInfo


class TestResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: str
    speed_ms: float
    memory_mb: float
    success_rate: float
    error_count: int
    tested_at: datetime


class CompatibilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client: str
    compatible: bool
    tested_at: datetime


class ServerDetailData(BaseModel):
    server: ServerRead
    test_results: List[TestResultRead]
    average_rating: float
    compatibilities: List[CompatibilityRead]


class ServerDetailResponse(BaseModel):
    status: str
    data: ServerDetailData


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    avatar_url: Optional[str] = None
    created_at: datetime


class RatingCreate(BaseModel):
    score: int = Field(ge=1, le=5)


class RatingDistributionBucket(BaseModel):
    score: int
    count: int


class RatingSummaryResponse(BaseModel):
    average_score: float
    total_ratings: int
    distribution: List[RatingDistributionBucket]
    my_score: Optional[int] = None


class ReviewCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10_000)


class ReviewRead(BaseModel):
    id: int
    title: str
    content: str
    helpful_count: int
    created_at: datetime
    updated_at: datetime
    author_username: str
    author_avatar_url: Optional[str] = None


class ReviewListResponse(BaseModel):
    status: str
    data: List[ReviewRead]
    pagination: PaginationInfo


class CompatibilityCreate(BaseModel):
    client: Literal["claude", "cursor", "vscode"]
    compatible: bool


class TestResultCreate(BaseModel):
    version: str
    speed_ms: float = Field(ge=0)
    memory_mb: float = Field(ge=0)
    success_rate: float = Field(ge=0, le=1)
    error_count: int = Field(ge=0)


class SyncRegistryResponse(BaseModel):
    status: str
    created: Optional[int] = None
    updated: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
