"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, useTransition } from "react";

import { Input } from "@/components/ui/input";
import { withParams } from "@/lib/utils";

const DEBOUNCE_MS = 400;

export function ServerSearchBar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentSearch = searchParams.get("search") ?? "";
  const [value, setValue] = useState(currentSearch);
  const [, startTransition] = useTransition();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );

  useEffect(() => {
    return () => clearTimeout(debounceRef.current);
  }, []);

  function handleChange(next: string) {
    setValue(next);
    clearTimeout(debounceRef.current);
    if (next === currentSearch) return;

    debounceRef.current = setTimeout(() => {
      const query = withParams(searchParams, {
        search: next || undefined,
        page: undefined,
      });
      startTransition(() => {
        router.push(`/servers?${query}`);
      });
    }, DEBOUNCE_MS);
  }

  return (
    <Input
      type="search"
      placeholder="Search servers by name or description…"
      value={value}
      onChange={(event) => handleChange(event.target.value)}
      className="max-w-md"
      aria-label="Search servers"
    />
  );
}
