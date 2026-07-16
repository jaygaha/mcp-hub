import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn, withParams } from "@/lib/utils";
import type { PaginationInfo } from "@/lib/types";

function PageLink({
  page,
  label,
  disabled,
  currentParams,
}: {
  page: number;
  label: string;
  disabled: boolean;
  currentParams: Record<string, string | undefined>;
}) {
  if (disabled) {
    return (
      <span
        className={cn(
          buttonVariants({ variant: "outline", size: "sm" }),
          "pointer-events-none opacity-50",
        )}
      >
        {label}
      </span>
    );
  }

  const query = withParams(currentParams, {
    page: page > 1 ? page : undefined,
  });

  return (
    <Link
      href={query ? `/servers?${query}` : "/servers"}
      className={buttonVariants({ variant: "outline", size: "sm" })}
    >
      {label}
    </Link>
  );
}

export function ServerPagination({
  pagination,
  currentParams,
}: {
  pagination: PaginationInfo;
  currentParams: Record<string, string | undefined>;
}) {
  const { skip, limit, total } = pagination;
  if (total === 0) return null;

  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <nav
      aria-label="Pagination"
      className="flex items-center justify-center gap-4 pt-4"
    >
      <PageLink
        page={currentPage - 1}
        label="Previous"
        disabled={currentPage <= 1}
        currentParams={currentParams}
      />
      <span className="text-muted-foreground text-sm">
        Page {currentPage.toLocaleString()} of {totalPages.toLocaleString()}
      </span>
      <PageLink
        page={currentPage + 1}
        label="Next"
        disabled={currentPage >= totalPages}
        currentParams={currentParams}
      />
    </nav>
  );
}
