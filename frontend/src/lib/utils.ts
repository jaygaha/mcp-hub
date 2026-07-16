import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// Merges `updates` into a copy of `current` (a live URLSearchParams or a plain searchParams-shaped object), dropping any key set to undefined.
// Shared by every /servers control (search, sort, pagination) so each one can change its own param without clobbering the others.
export function withParams(
  current: URLSearchParams | Record<string, string | undefined>,
  updates: Record<string, string | number | undefined>,
): string {
  const params =
    current instanceof URLSearchParams
      ? new URLSearchParams(current)
      : new URLSearchParams(
        Object.entries(current).filter(
          (entry): entry is [string, string] => entry[1] !== undefined,
        ),
      );

  for (const [key, value] of Object.entries(updates)) {
    if (value === undefined) {
      params.delete(key);
    } else {
      params.set(key, String(value));
    }
  }

  return params.toString();
}
