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

const ANY = "any";
const OPTIONS = ["4", "3", "2"];

export function ServerRatingFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const minRating = searchParams.get("min_rating") ?? ANY;

  function handleChange(next: string | null) {
    if (!next || next === minRating) return;
    const query = withParams(searchParams, {
      min_rating: next === ANY ? undefined : next,
      page: undefined,
    });
    router.push(`/servers?${query}`);
  }

  return (
    <Select value={minRating} onValueChange={handleChange}>
      <SelectTrigger aria-label="Filter by minimum rating" className="w-36">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ANY}>Any rating</SelectItem>
        {OPTIONS.map((option) => (
          <SelectItem key={option} value={option}>
            {option}+ stars
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
