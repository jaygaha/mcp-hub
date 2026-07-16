import { ResultsSummary } from "@/components/servers/results-summary";
import { ServerGrid } from "@/components/servers/server-grid";
import { ServerPagination } from "@/components/servers/server-pagination";
import { ServerSearchBar } from "@/components/servers/server-search-bar";
import { ServerSortSelect } from "@/components/servers/server-sort-select";
import { getServers } from "@/lib/api";
import type { SortOption } from "@/lib/types";

const PAGE_SIZE = 20;
const VALID_SORTS: SortOption[] = ["popular", "newest", "trending"];

export default async function ServersPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; sort?: string; page?: string }>;
}) {
  const params = await searchParams;
  const search = params.search?.trim() || undefined;
  const sort = VALID_SORTS.includes(params.sort as SortOption)
    ? (params.sort as SortOption)
    : "popular";
  const page = Math.max(1, Number(params.page) || 1);
  const skip = (page - 1) * PAGE_SIZE;

  const { data: servers, pagination } = await getServers({
    search,
    sort,
    skip,
    limit: PAGE_SIZE,
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
        <ServerSortSelect />
      </div>

      <ResultsSummary pagination={pagination} search={search} />

      <ServerGrid servers={servers} />

      <ServerPagination pagination={pagination} currentParams={params} />
    </div>
  );
}
