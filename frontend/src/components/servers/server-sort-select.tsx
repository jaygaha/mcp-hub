"use client";

import { useRouter, useSearchParams } from "next/navigation";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { withParams } from "@/lib/utils";
import type { SortOption } from "@/lib/types";

const SORT_LABELS: Record<SortOption, string> = {
  popular: "Popular",
  newest: "Newest",
  trending: "Trending",
};

export function ServerSortSelect() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sort = (searchParams.get("sort") as SortOption | null) ?? "popular";

  function handleChange(next: string | null) {
    if (!next || next === sort) return;
    const query = withParams(searchParams, { sort: next, page: undefined });
    router.push(`/servers?${query}`);
  }

  return (
    <Select value={sort} onValueChange={handleChange}>
      <SelectTrigger aria-label="Sort servers" className="w-40">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {(Object.keys(SORT_LABELS) as SortOption[]).map((option) => (
          <SelectItem key={option} value={option}>
            {SORT_LABELS[option]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
