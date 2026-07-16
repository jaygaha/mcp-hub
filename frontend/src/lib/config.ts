// Server-only. No NEXT_PUBLIC_ prefix, so this is never bundled to the
// browser: Server Components fetch the backend directly; nothing
// client-side ever needs (or should know) this address.
export const BACKEND_INTERNAL_URL =
  process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
