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

`GET /servers/<unknown-namespace>` on the frontend renders the correct
not-found UI (verified), but the actual HTTP status code is 200, not 404.
This is documented Next.js behavior, not a bug in this app: the root
layout has no data dependency, so the App Router starts streaming the
response shell (locking in a 200) before `notFound()` - called after
`await getServerByNamespace(...)` - can run. Once streaming starts, the
status code can't change; Next.js compensates by injecting a `noindex`
meta tag automatically, so search engines don't index these URLs despite
the 200.

This only matters if something checks the raw status code (uptime
monitors, non-browser API-style consumers of these HTML pages). The
documented fix is to pre-check existence in `proxy` (this version's name
for middleware) before the page ever renders, returning a real 404 there
- but that means an extra backend round trip on every detail-page view
to buy a correct status code on the (currently nonexistent-server) error
path. Not worth it yet; revisit if something downstream actually needs
the real status code.
