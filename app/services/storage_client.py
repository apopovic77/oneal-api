"""
Storage API Client for O'Neal Product API
Handles batch resolution of media variants from Storage API
"""

import httpx
import os
from typing import Dict, List, Optional
from functools import lru_cache


class StorageClient:
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv("STORAGE_API_URL", "https://api-storage.arkturian.com")
        self.api_key = api_key or os.getenv("STORAGE_API_KEY", "Inetpass1")
        self.timeout = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)

    async def get_variants_batch(self, queries: List[Dict[str, str]]) -> Dict[str, Dict]:
        """
        Batch resolve asset variants from Storage API.

        Args:
            queries: List of {"link_id": str, "role": str (optional)} queries

        Returns:
            Dict mapping link_id to asset data:
            {
                "MX-2026-001-HERO": {
                    "id": 81,
                    "type": "image",
                    "role": "hero",
                    "variants": {"thumb": "...", "preview": "...", "print": "..."},
                    "width": 4096,
                    "height": 3072,
                    ...
                }
            }
        """
        if not queries:
            return {}

        url = f"{self.base_url}/storage/asset-refs/batch"
        payload = {"queries": queries}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"X-API-Key": self.api_key, "Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", {})
            except httpx.HTTPStatusError as e:
                print(f"Storage API HTTP error: {e.response.status_code} - {e.response.text}")
                return {}
            except httpx.RequestError as e:
                print(f"Storage API request error: {e}")
                return {}
            except Exception as e:
                print(f"Storage API unexpected error: {e}")
                return {}

    async def get_variants(self, link_id: str, role: Optional[str] = None) -> Optional[Dict]:
        """
        Get variants for a single link_id (convenience method).

        Args:
            link_id: Link ID to resolve
            role: Optional role filter (hero/detail/lifestyle)

        Returns:
            Asset data dict or None if not found
        """
        query = {"link_id": link_id}
        if role:
            query["role"] = role

        results = await self.get_variants_batch([query])
        return results.get(link_id)


# Singleton instance
storage_client = StorageClient()


# Optional: Add caching for frequently accessed assets
@lru_cache(maxsize=500)
def _cache_key(link_ids_tuple: tuple) -> str:
    """Generate cache key from sorted link_ids"""
    return "|".join(sorted(link_ids_tuple))


async def get_variants_batch_cached(link_ids: List[str]) -> Dict[str, Dict]:
    """
    Cached version of batch variants lookup.
    Cache expires when process restarts (good enough for v1).
    """
    # For now, just pass through to non-cached version
    # In production, you could implement Redis caching here
    queries = [{"link_id": link_id} for link_id in link_ids]
    return await storage_client.get_variants_batch(queries)
