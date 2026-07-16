from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


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


class SyncRegistryResponse(BaseModel):
    status: str
    created: Optional[int] = None
    updated: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
