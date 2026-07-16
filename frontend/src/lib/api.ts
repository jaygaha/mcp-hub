import { notFound } from "next/navigation";

import { BACKEND_INTERNAL_URL } from "@/lib/config";
import type {
  ApiErrorBody,
  ServerDetailResponse,
  ServerListParams,
  ServerListResponse,
} from "@/lib/types";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    return body.detail || response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function getServers(
  params: ServerListParams = {},
  // Search/sort/pagination results are per-request and must stay fresh, so no-store is the default. Callers with a fixed, visitor-independent
  // query (e.g. the homepage's trending list) can pass a revalidate window instead to let Next cache the response - the registry only syncs every
  // ~20 min (see TODO.md), so a minute of staleness is a non-issue.
  { revalidate }: { revalidate?: number } = {},
): Promise<ServerListResponse> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.sort) query.set("sort", params.sort);
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.skip !== undefined) query.set("skip", String(params.skip));

  const response = await fetch(
    `${BACKEND_INTERNAL_URL}/api/v1/servers?${query.toString()}`,
    revalidate !== undefined ? { next: { revalidate } } : { cache: "no-store" },
  );

  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }

  return response.json() as Promise<ServerListResponse>;
}

// `namespace` is interpolated raw (not encodeURIComponent'd) because it contains slashes (e.g. "ac.inference.sh/mcp") that must stay literal
// path segments to match the backend's {namespace:path} route.
export async function getServerByNamespace(
  namespace: string,
): Promise<ServerDetailResponse> {
  const response = await fetch(
    `${BACKEND_INTERNAL_URL}/api/v1/servers/${namespace}`,
    { cache: "no-store" },
  );

  if (response.status === 404) {
    notFound();
  }

  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }

  return response.json() as Promise<ServerDetailResponse>;
}
