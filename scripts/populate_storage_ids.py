#!/usr/bin/env python3
"""
Populate storage_id fields in products.json by matching with Storage API.

This script:
1. Loads products.json
2. Fetches all O'Neal storage objects via requests (with SSL verification disabled)
3. Matches media items with storage objects based on:
   - product_id in context
   - media_id in context
   - external_uri matching
4. Updates storage_id fields
5. Saves updated products.json
"""

import json
import requests
import urllib3
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

# Disable SSL warnings (for self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
PRODUCTS_JSON = Path(__file__).parent.parent / "app" / "data" / "products.json"
STORAGE_API_URL = "https://api-storage.arkturian.com/storage/list"
API_KEY = "oneal_demo_token"


def fetch_storage_objects() -> List[Dict]:
    """Fetch all O'Neal storage objects using requests."""
    print("🔍 Fetching O'Neal storage objects from Storage API...")
    
    all_objects = []
    offset = 0
    limit = 100
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "mine": "false"  # Get all O'Neal tenant objects (not just owned by API key user)
        }
        
        try:
            response = requests.get(
                STORAGE_API_URL,
                headers=headers,
                params=params,
                verify=False,  # Disable SSL verification for self-signed certs
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ⚠️  API error: {response.status_code}")
                break
            
            data = response.json()
            items = data.get("items", [])  # Storage API uses "items", not "results"

            if not items:
                break

            all_objects.extend(items)
            print(f"  Fetched {len(all_objects)} objects so far...")
            
            # Check if we've fetched all
            total = data.get("total", 0)
            if len(all_objects) >= total or len(items) < limit:
                break
            
            offset += limit
            
        except Exception as e:
            print(f"  ⚠️  Error fetching: {e}")
            break
    
    print(f"✅ Fetched {len(all_objects)} total storage objects\n")
    return all_objects


def normalize_url(url: str) -> str:
    """Normalize URL for comparison (remove query params, lowercase)."""
    parsed = urlparse(url)
    # Remove query params and fragment
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return normalized.lower()


def build_storage_mappings(storage_objects: List[Dict]) -> tuple[Dict[str, int], Dict[str, int]]:
    """
    Build multiple mappings for matching:
    1. context → storage_id
    2. normalized_external_uri → storage_id
    """
    print("🗺️  Building storage mappings...")
    
    context_map = {}
    uri_map = {}
    
    for obj in storage_objects:
        storage_id = obj.get("id")
        context = obj.get("context")
        external_uri = obj.get("external_uri")
        
        if not storage_id:
            continue
        
        # Map context
        if context:
            context_map[context] = storage_id
            
            # Also try to extract product_id from context
            # Format: "oneal_product_{product_id}"
            if context.startswith("oneal_product_"):
                product_id = context.replace("oneal_product_", "")
                context_map[product_id] = storage_id
        
        # Map external URI
        if external_uri:
            normalized = normalize_url(external_uri)
            uri_map[normalized] = storage_id
    
    print(f"  ✅ Context mappings: {len(context_map)}")
    print(f"  ✅ URI mappings: {len(uri_map)}\n")
    
    return context_map, uri_map


def match_media_to_storage(
    product_id: str,
    media: Dict,
    context_map: Dict[str, int],
    uri_map: Dict[str, int]
) -> Optional[int]:
    """
    Try to match a media item to a storage object.
    
    Matching strategies (in order):
    1. Direct media_id match in context
    2. Product_id match in context
    3. External URI match
    """
    media_id = media.get("id")
    src_url = str(media.get("src", ""))
    
    # Strategy 1: Direct media_id match
    if media_id and media_id in context_map:
        return context_map[media_id]
    
    # Strategy 2: Product_id match
    if product_id in context_map:
        return context_map[product_id]
    
    # Strategy 3: Try with oneal_product_ prefix
    prefixed_product_id = f"oneal_product_{product_id}"
    if prefixed_product_id in context_map:
        return context_map[prefixed_product_id]
    
    # Strategy 4: External URI match
    if src_url:
        normalized = normalize_url(src_url)
        if normalized in uri_map:
            return uri_map[normalized]
    
    return None


def populate_storage_ids(
    products: List[Dict],
    context_map: Dict[str, int],
    uri_map: Dict[str, int]
) -> tuple[int, int]:
    """Populate storage_id fields in products."""
    print("📝 Populating storage_ids...")
    
    total_media = 0
    matched_media = 0
    
    for product in products:
        product_id = product.get("id")
        media_list = product.get("media", [])
        
        for media in media_list:
            total_media += 1
            
            # Skip if already has storage_id
            if media.get("storage_id"):
                matched_media += 1
                continue
            
            # Try to match
            storage_id = match_media_to_storage(
                product_id,
                media,
                context_map,
                uri_map
            )
            
            if storage_id:
                media["storage_id"] = storage_id
                matched_media += 1
            else:
                # Keep as null
                media["storage_id"] = None
                print(f"  ⚠️  No match for: {product_id} / {media.get('id')}")
    
    match_rate = (matched_media / total_media * 100) if total_media > 0 else 0
    print(f"\n✅ Matched {matched_media}/{total_media} media items ({match_rate:.1f}%)\n")
    
    return total_media, matched_media


def main():
    print("🚀 Starting storage_id population process...\n")
    
    # 1. Load products.json
    print(f"📖 Loading products from: {PRODUCTS_JSON}")
    with PRODUCTS_JSON.open("r", encoding="utf-8") as f:
        products = json.load(f)
    print(f"✅ Loaded {len(products)} products\n")
    
    # 2. Fetch storage objects
    storage_objects = fetch_storage_objects()
    
    if not storage_objects:
        print("❌ No storage objects fetched. Aborting.")
        return
    
    # 3. Build mappings
    context_map, uri_map = build_storage_mappings(storage_objects)
    
    # 4. Populate storage_ids
    total, matched = populate_storage_ids(products, context_map, uri_map)
    
    # 5. Save updated products.json
    print(f"💾 Saving updated products.json...")
    
    # Create backup
    backup_path = PRODUCTS_JSON.with_suffix(".json.backup2")
    import shutil
    shutil.copy2(PRODUCTS_JSON, backup_path)
    print(f"  📦 Backup saved to: {backup_path}")
    
    # Save updated file
    with PRODUCTS_JSON.open("w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved updated products.json")
    
    print(f"\n🎉 Done! Populated storage_id for {matched}/{total} media items")
    
    if matched < total:
        print(f"\n💡 {total - matched} media items still have null storage_id")
        print(f"   These may need manual matching or the images aren't in Storage API yet")


if __name__ == "__main__":
    main()

