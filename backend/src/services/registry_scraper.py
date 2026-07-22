import asyncio
from datetime import datetime

import httpx2
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models import MCPServer, utcnow
from src.config import settings
import logging

logger = logging.getLogger(__name__)

# item["_meta"][OFFICIAL_META_KEY]["isLatest"] marks the current version of a namespace.
OFFICIAL_META_KEY = "io.modelcontextprotocol.registry/official"

_MAX_RETRIES = 5
# A full sync makes hundreds of sequential requests; pace them so we don't
# trip the registry's rate limit in the first place.
_PAGE_DELAY_SECONDS = 0.2
# Upserts are chunked instead of one-row-at-a-time to cut ~16.7k servers
# down from ~33k Postgres round trips to ~2 per batch, and each batch
# commits independently so a crash mid-sync doesn't lose everything.
_BATCH_SIZE = 500


async def _get_json_with_retry(client: httpx2.AsyncClient, url: str, **kwargs) -> dict:
    """Retries transient failures (timeouts, 5xx, 429) instead of discarding
    everything fetched so far in a hundreds-of-pages walk over one bad
    request. 429 honors Retry-After when the server sends one."""
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.json()
        except (httpx2.TransportError, httpx2.HTTPStatusError) as exc:
            status = (
                exc.response.status_code
                if isinstance(exc, httpx2.HTTPStatusError)
                else None
            )
            retryable = status is None or status == 429 or status >= 500
            if not retryable or attempt == _MAX_RETRIES:
                raise
            retry_after = status == 429 and exc.response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else 2**attempt
            logger.warning(
                "Registry request to %s failed (attempt %d/%d): %s - retrying in %.1fs",
                url,
                attempt + 1,
                _MAX_RETRIES + 1,
                exc,
                wait,
            )
            await asyncio.sleep(wait)


def _extract_repository_url(server_data: dict) -> str | None:
    """websiteUrl is the canonical URL field; repository is an object
    ({"url": ..., "source": ...}), never a plain string."""
    website_url = server_data.get("websiteUrl")
    if website_url:
        return website_url

    repository = server_data.get("repository")
    if isinstance(repository, dict):
        return repository.get("url")
    if isinstance(repository, str):
        return repository
    return None


def _extract_docker_image(server_data: dict) -> str | None:
    """Pull an OCI/Docker install target out of the registry's `packages` array."""
    for package in server_data.get("packages") or []:
        if package.get("registryType") not in ("oci", "docker"):
            continue
        identifier = package.get("identifier")
        version = package.get("version")
        if identifier and version:
            return f"{identifier}:{version}"
        return identifier
    return None


def _server_row(server_data: dict, now: datetime) -> dict:
    """Row dict for one registry entry, ready for a bulk INSERT. A raw Core
    insert (unlike constructing an MCPServer(...) instance) bypasses
    SQLModel's default_factory=utcnow, so created_at/updated_at must be set
    explicitly here."""
    namespace = server_data["name"]
    return {
        "namespace": namespace,
        "name": server_data.get("title") or namespace,
        "description": server_data.get("description"),
        "repository_url": _extract_repository_url(server_data),
        "docker_image": _extract_docker_image(server_data),
        "version": server_data.get("version") or "latest",
        "author": server_data.get("author")
        or (namespace.split("/")[0] if "/" in namespace else namespace),
        "official_registry_id": namespace,
        "created_at": now,
        "updated_at": now,
    }


class RegistryScraper:
    def __init__(self):
        self.registry_url = settings.official_registry_url

    async def _fetch_latest_servers(self, client: httpx2.AsyncClient) -> list[dict]:
        """Walk every page via the cursor, keeping only each namespace's
        latest version (the registry lists every historical version)."""
        latest_by_namespace: dict[str, dict] = {}
        cursor = None

        while True:
            url = f"{self.registry_url}/servers"
            params = {"cursor": cursor} if cursor else None
            page = await _get_json_with_retry(client, url, params=params)

            for item in page.get("servers", []):
                server_data = item.get("server", {})
                namespace = server_data.get("name")
                if not namespace:
                    continue

                is_latest = (
                    item.get("_meta", {}).get(OFFICIAL_META_KEY, {}).get("isLatest")
                )
                if namespace not in latest_by_namespace or is_latest:
                    latest_by_namespace[namespace] = server_data

            cursor = page.get("metadata", {}).get("nextCursor")
            if not cursor:
                break
            await asyncio.sleep(_PAGE_DELAY_SECONDS)

        return list(latest_by_namespace.values())

    async def sync_all_servers(self, db: AsyncSession) -> dict:
        try:
            async with httpx2.AsyncClient(timeout=30.0) as client:
                servers = await self._fetch_latest_servers(client)

            created_count = 0
            updated_count = 0

            for i in range(0, len(servers), _BATCH_SIZE):
                batch = servers[i : i + _BATCH_SIZE]
                now = utcnow()
                rows = [_server_row(server_data, now) for server_data in batch]
                namespaces = [row["namespace"] for row in rows]

                existing_namespaces = (
                    await db.execute(
                        select(MCPServer.namespace).where(
                            MCPServer.namespace.in_(namespaces)
                        )
                    )
                ).scalars().all()

                # Bulk upsert: unlike the single-row upserts elsewhere (reviews.py,
                # benchmarks.py) where set_ takes literal Python values, each row
                # in this batch has its own incoming values - set_ must reference
                # insert_stmt.excluded so a conflicting row updates with its own
                # data, not one shared value across the whole batch.
                insert_stmt = pg_insert(MCPServer).values(rows)
                stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["namespace"],
                    set_={
                        "name": insert_stmt.excluded.name,
                        "description": insert_stmt.excluded.description,
                        "repository_url": insert_stmt.excluded.repository_url,
                        "docker_image": insert_stmt.excluded.docker_image,
                        "version": insert_stmt.excluded.version,
                        "author": insert_stmt.excluded.author,
                        "official_registry_id": insert_stmt.excluded.official_registry_id,
                        "updated_at": insert_stmt.excluded.updated_at,
                    },
                )
                await db.execute(stmt)
                await db.commit()

                updated_count += len(existing_namespaces)
                created_count += len(rows) - len(existing_namespaces)

            return {
                "status": "success",
                "created": created_count,
                "updated": updated_count,
                "total": created_count + updated_count,
            }

        except Exception:
            logger.exception("Error syncing registry")
            await db.rollback()
            return {
                "status": "error",
                "message": "Failed to sync registry. See server logs for details.",
            }

    async def update_server(self, namespace: str, db: AsyncSession) -> dict:
        try:
            import urllib.parse

            safe_namespace = urllib.parse.quote(namespace, safe="")
            async with httpx2.AsyncClient(timeout=30.0) as client:
                url = f"{self.registry_url}/servers/{safe_namespace}/versions/latest"
                data = await _get_json_with_retry(client, url)
                server_data = data.get("server", data)

                stmt = select(MCPServer).where(MCPServer.namespace == namespace)
                result = await db.execute(stmt)
                server = result.scalars().first()

                if not server:
                    return {"status": "error", "message": "Server not found"}

                server.description = server_data.get("description")
                server.repository_url = _extract_repository_url(server_data)
                server.docker_image = _extract_docker_image(server_data)
                server.version = server_data.get("version") or server.version
                server.author = server_data.get("author") or (
                    namespace.split("/")[0] if "/" in namespace else namespace
                )
                server.updated_at = utcnow()

                await db.commit()

                return {"status": "success", "message": "Server updated"}

        except Exception:
            logger.exception("Error updating server %s", namespace)
            await db.rollback()
            return {
                "status": "error",
                "message": "Failed to update server. See server logs for details.",
            }
