# TODO

## Registry sync is now fetch-bound, not DB-bound

`RegistryScraper.sync_all_servers` used to do one SELECT-then-INSERT/UPDATE per server in a single un-batched transaction (~33k round trips for ~16.7k servers). Fixed: upserts are now chunked (`_BATCH_SIZE = 500`, `INSERT ... ON CONFLICT DO UPDATE`), committing per batch - a benchmark against 5,000 synthetic servers (mocked registry response, real Postgres) wrote all of them in under a second, so the DB side of a full sync is now on the order of a few seconds, not ~20 minutes.

Verified live on 2026-07-21: re-running `make sync-registry` against the real registry took well over 10 minutes, but the entire time was spent in `_fetch_latest_servers` (paginating the real registry over the network, `_PAGE_DELAY_SECONDS = 0.2` between pages) - the DB-write phase was never the thing running long during that call. So the next bottleneck, if a full sync's wall-clock time matters again, is the fetch phase (page count and network latency), not Postgres. Not addressed here - out of scope for the batching fix, and the registry's own pagination/rate-limit behavior isn't something this app controls.

## Frontend Docker image is dev-only

`frontend/Dockerfile` just runs `npm run dev` against a bind-mounted volume - same posture as the backend today (`uvicorn --reload`), not a lesser standard, but neither has a real production build/image yet. Worth a multi-stage build (`next build` + `next start`, or `output: "standalone"`) before deploying either service anywhere real.

## Server detail page 404s return HTTP 200

`GET /servers/<unknown-namespace>` on the frontend renders the correct not-found UI (verified), but the actual HTTP status code is 200, not 404. This is documented Next.js behavior, not a bug in this app: the root layout has no data dependency, so the App Router starts streaming the response shell (locking in a 200) before `notFound()` - called after `await getServerByNamespace(...)` - can run. Once streaming starts, the status code can't change; Next.js compensates by injecting a `noindex` meta tag automatically, so search engines don't index these URLs despite the 200.

This only matters if something checks the raw status code (uptime monitors, non-browser API-style consumers of these HTML pages). The documented fix is to pre-check existence in `proxy` (this version's name for middleware) before the page ever renders, returning a real 404 there - but that means an extra backend round trip on every detail-page view to buy a correct status code on the (currently nonexistent-server) error path. Not worth it yet; revisit if something downstream actually needs the real status code.

## Auth cookie assumes same-domain-different-port deployment

The GitHub OAuth session cookie relies on cookie scoping ignoring port (RFC 6265) - a cookie set by the backend on `localhost` is automatically visible to the frontend on a different `localhost` port in local dev, so no cross-origin cookie configuration was needed for Day 3. This breaks once frontend and backend sit on genuinely different domains in a real deployment (not just different ports), which will need explicit cookie-domain / reverse-proxy configuration. Not addressed since there's no production deployment yet (see the frontend-Docker-image entry above).

## No rating/review moderation, rate-limiting, or JWT refresh

Any authenticated GitHub account can rate or review a server with no throttling and no content checks beyond the 1-5 score bound and a length cap on review text - matches the original planning doc's own depth, not fixed here. Sessions hard-expire 30 days after login (no refresh-token flow), so that's a full re-login, not a silent extension.

## `Review.helpful_count` stays inert

The column exists (from Day 1's model scaffolding) but nothing increments it - no helpfulness-voting endpoint was built, since it was never in the original plan beyond a bare field.

## `SiteHeader` reading the auth cookie forces every route dynamic

Checking the login cookie via `next/headers` in the header (used on every page) opts every route, including the homepage, out of static rendering - there's no partial-prerendering flag enabled in `next.config.ts` to let the static shell and the dynamic auth check coexist. Matches this app's existing reality that most routes already fetch with `cache: "no-store"`; revisit only if homepage load time becomes a real concern.

## GitHub username rename can collide on login

`users.username` is unique; if a GitHub user renames to a name some other local account already has, `get_or_create_user` will raise on commit instead of resolving the conflict. Rare, unhandled.

## No test-execution engine behind compatibility/benchmarks

`POST .../compatibility` and `.../test-results` (backend/src/api/benchmarks.py) just record whatever the caller sends - nothing in this codebase actually pulls a server's `docker_image` and runs it to produce these numbers. That's a much larger, riskier undertaking (executing untrusted third-party code) and was intentionally left out of scope. These endpoints exist for a human or a future separate test-runner to report results into.

## Compatibility client set is coupled to the frontend

`CompatibilityCreate.client` is a `Literal["claude", "cursor", "vscode"]` (backend/src/api/schemas.py), matching `KNOWN_CLIENTS` hardcoded in `frontend/src/components/servers/compatibility-matrix.tsx`. Adding a fourth client means updating both together - there's no shared source of truth for the client list today.
