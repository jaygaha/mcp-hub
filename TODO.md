# TODO

## Registry sync: one giant transaction + N+1 queries

`RegistryScraper.sync_all_servers` (src/services/registry_scraper.py) does one SELECT-then-INSERT/UPDATE per server, all inside a single session that only commits at the very end. Against the real registry (currently ~16.7k servers) that's ~33k round trips to Postgres in one transaction, and the run takes about 20 minutes.

It works, but:
- Nothing is visible in the table until the very last commit - no
  incremental progress, and a crash mid-run loses everything.
- Holding one transaction open that long isn't great for Postgres (locks,
  bloat).
- All those round trips are the real bottleneck, not the registry HTTP calls.

Fix would be something like: batch the upserts (`INSERT ... ON CONFLICT DO UPDATE`, chunked), and commit per batch instead of once at the end.

Found while re-running `make sync-registry` on 2026-07-15 after fixing the 429/rate-limit issue - the full sync finally completed (created: 16702, updated: 0), which is what surfaced this.
