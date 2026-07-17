# TODO

## Registry sync: one giant transaction + N+1 queries

`RegistryScraper.sync_all_servers` (backend/src/services/registry_scraper.py) does one SELECT-then-INSERT/UPDATE per server, all inside a single session that only commits at the very end. Against the real registry (currently ~16.7k servers) that's ~33k round trips to Postgres in one transaction, and the run takes about 20 minutes.

It works, but:
- Nothing is visible in the table until the very last commit - no
  incremental progress, and a crash mid-run loses everything.
- Holding one transaction open that long isn't great for Postgres (locks,
  bloat).
- All those round trips are the real bottleneck, not the registry HTTP calls.

Fix would be something like: batch the upserts (`INSERT ... ON CONFLICT DO UPDATE`, chunked), and commit per batch instead of once at the end.

Found while re-running `make sync-registry` on 2026-07-15 after fixing the 429/rate-limit issue - the full sync finally completed (created: 16702, updated: 0), which is what surfaced this.

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
