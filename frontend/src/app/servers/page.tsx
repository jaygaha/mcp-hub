import { CLIENT_LABELS } from "@/components/servers/compatibility-badge";
import { ResultsSummary } from "@/components/servers/results-summary";
import { ServerCompatibilityFilter } from "@/components/servers/server-compatibility-filter";
import { ServerGrid } from "@/components/servers/server-grid";
import { ServerPagination } from "@/components/servers/server-pagination";
import { ServerRatingFilter } from "@/components/servers/server-rating-filter";
import { ServerSearchBar } from "@/components/servers/server-search-bar";
import { ServerSortSelect } from "@/components/servers/server-sort-select";
import { getServers } from "@/lib/api";
import type { CompatibilityClient, SortOption } from "@/lib/types";

const PAGE_SIZE = 20;
const VALID_SORTS: SortOption[] = ["popular", "newest", "trending", "rating"];
const VALID_MIN_RATINGS = ["4", "3", "2"];

export default async function ServersPage({
  searchParams,
}: {
  searchParams: Promise<{
    search?: string;
    sort?: string;
    page?: string;
    min_rating?: string;
    client?: string;
  }>;
}) {
  const params = await searchParams;
  const search = params.search?.trim() || undefined;
  const sort = VALID_SORTS.includes(params.sort as SortOption)
    ? (params.sort as SortOption)
    : "popular";
  const page = Math.max(1, Number(params.page) || 1);
  const skip = (page - 1) * PAGE_SIZE;
  const minRating = VALID_MIN_RATINGS.includes(params.min_rating ?? "")
    ? Number(params.min_rating)
    : undefined;
  const client = Object.keys(CLIENT_LABELS).includes(params.client ?? "")
    ? (params.client as CompatibilityClient)
    : undefined;

  const { data: servers, pagination } = await getServers({
    search,
    sort,
    skip,
    limit: PAGE_SIZE,
    min_rating: minRating,
    client,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Browse servers</h1>
        <p className="text-muted-foreground text-sm">
          Search the official MCP registry.
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <ServerSearchBar />
        <div className="flex flex-wrap gap-2">
          <ServerRatingFilter />
          <ServerCompatibilityFilter />
          <ServerSortSelect />
        </div>
      </div>

      <ResultsSummary pagination={pagination} search={search} />

      <ServerGrid servers={servers} />

      <ServerPagination pagination={pagination} currentParams={params} />
    </div>
  );
}
