import type { PaginationInfo } from "@/lib/types";

export function ResultsSummary({
  pagination,
  search,
}: {
  pagination: PaginationInfo;
  search?: string;
}) {
  const { skip, limit, total } = pagination;

  if (total === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        {search ? `No servers match "${search}".` : "No servers found."}
      </p>
    );
  }

  const from = skip + 1;
  const to = Math.min(skip + limit, total);

  return (
    <p className="text-muted-foreground text-sm">
      Showing {from.toLocaleString()}–{to.toLocaleString()} of{" "}
      {total.toLocaleString()} servers
      {search ? ` for "${search}"` : ""}
    </p>
  );
}
