// 1:1 mirror of backend/src/api/schemas.py. datetimes serialize as ISO 8601
// strings over JSON, so they're typed as `string` here, not `Date`.

export interface ServerRead {
  id: number;
  namespace: string;
  name: string;
  description: string | null;
  repository_url: string | null;
  author: string | null;
  official_registry_id: string | null;
  version: string | null;
  docker_image: string | null;
  created_at: string;
  updated_at: string;
}

export interface ServerListItem extends ServerRead {
  average_rating: number;
  total_ratings: number;
}

export interface PaginationInfo {
  skip: number;
  limit: number;
  total: number;
}

export interface ServerListResponse {
  status: string;
  data: ServerListItem[];
  pagination: PaginationInfo;
}

export interface TestResultRead {
  id: number;
  version: string;
  speed_ms: number;
  memory_mb: number;
  success_rate: number;
  error_count: number;
  tested_at: string;
}

// `client` is a free string in the DB, but only these three values are ever
// written today (see backend/src/db/models.py's CompatibilityBase comment).
export type CompatibilityClient = "claude" | "cursor" | "vscode";

export interface CompatibilityRead {
  id: number;
  client: CompatibilityClient;
  compatible: boolean;
  tested_at: string;
}

export interface ServerDetailData {
  server: ServerRead;
  test_results: TestResultRead[];
  average_rating: number;
  compatibilities: CompatibilityRead[];
}

export interface ServerDetailResponse {
  status: string;
  data: ServerDetailData;
}

export type SortOption = "popular" | "newest" | "trending" | "rating";

export interface ServerListParams {
  search?: string;
  sort?: SortOption;
  limit?: number;
  skip?: number;
  min_rating?: number;
  client?: CompatibilityClient;
}

// FastAPI's default HTTPException body shape.
export interface ApiErrorBody {
  detail: string;
}

export interface UserRead {
  id: number;
  username: string;
  avatar_url: string | null;
  created_at: string;
}

export interface RatingCreate {
  score: number;
}

export interface RatingDistributionBucket {
  score: number;
  count: number;
}

export interface RatingSummaryResponse {
  average_score: number;
  total_ratings: number;
  distribution: RatingDistributionBucket[];
  my_score: number | null;
}

export interface ReviewCreate {
  title: string;
  content: string;
}

export interface ReviewRead {
  id: number;
  title: string;
  content: string;
  helpful_count: number;
  created_at: string;
  updated_at: string;
  author_username: string;
  author_avatar_url: string | null;
}

export interface ReviewListResponse {
  status: string;
  data: ReviewRead[];
  pagination: PaginationInfo;
}
