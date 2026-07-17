// Server-only. No NEXT_PUBLIC_ prefix, so this is never bundled to the
// browser: Server Components fetch the backend directly; nothing
// client-side ever needs (or should know) this address.
export const BACKEND_INTERNAL_URL =
  process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";

// Public on purpose - the GitHub OAuth flow is a top-level browser redirect,
// not a fetch, so it needs a URL the browser can actually navigate to. This
// is the externally-mapped backend address (e.g. http://localhost:8000),
// never the Docker-internal hostname BACKEND_INTERNAL_URL uses.
const PUBLIC_BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export const GITHUB_LOGIN_URL = `${PUBLIC_BACKEND_URL}/api/v1/auth/login`;
export const LOGOUT_URL = `${PUBLIC_BACKEND_URL}/api/v1/auth/logout`;
