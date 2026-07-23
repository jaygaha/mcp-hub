"use client";

import { useRouter, useSearchParams } from "next/navigation";

import { CLIENT_LABELS } from "@/components/servers/compatibility-badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { withParams } from "@/lib/utils";
import type { CompatibilityClient } from "@/lib/types";

const ANY = "any";

export function ServerCompatibilityFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const client = searchParams.get("client") ?? ANY;

  function handleChange(next: string | null) {
    if (!next || next === client) return;
    const query = withParams(searchParams, {
      client: next === ANY ? undefined : next,
      page: undefined,
    });
    router.push(`/servers?${query}`);
  }

  return (
    <Select value={client} onValueChange={handleChange}>
      <SelectTrigger aria-label="Filter by client compatibility" className="w-44">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ANY}>Any client</SelectItem>
        {(Object.keys(CLIENT_LABELS) as CompatibilityClient[]).map((option) => (
          <SelectItem key={option} value={option}>
            {CLIENT_LABELS[option]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
