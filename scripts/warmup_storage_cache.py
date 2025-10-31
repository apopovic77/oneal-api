#!/usr/bin/env python3
"""
Warmup Storage API cache by pre-loading all O'Neal product images.

Downloads each image in two resolutions:
1. Thumbnail: 400px width, WebP, 75% quality
2. Full: 1200px width, WebP, 85% quality

This ensures fast loading in the Product Finder app.
"""

import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

STORAGE_API = "https://api-storage.arkturian.com"
STORAGE_API_KEY = "oneal_demo_token"  # O'Neal tenant API key
PRODUCTS_JSON = Path(__file__).parent.parent / "app/data/products.json"

# Two image resolutions for Product Finder
RESOLUTIONS = [
    {"name": "thumbnail", "params": "?width=400&format=webp&quality=75"},
    {"name": "full", "params": "?width=1200&format=webp&quality=85"}
]

def warmup_image(storage_id: int, resolution: dict):
    """Download a single image to warmup cache."""
    url = f"{STORAGE_API}/storage/media/{storage_id}{resolution['params']}"
    headers = {'X-API-KEY': STORAGE_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=60)  # Increased timeout for large images
        response.raise_for_status()
        size_kb = len(response.content) / 1024
        return True, storage_id, resolution['name'], size_kb
    except Exception as e:
        return False, storage_id, resolution['name'], str(e)

def main():
    print("=" * 80)
    print("O'NEAL STORAGE CACHE WARMUP")
    print("=" * 80)

    # Load products.json
    print(f"\n📂 Loading {PRODUCTS_JSON}...")
    with open(PRODUCTS_JSON, 'r') as f:
        products = json.load(f)

    # Collect all storage_ids
    storage_ids = set()
    for product in products:
        for media in product.get('media', []):
            sid = media.get('storage_id')
            if sid:
                storage_ids.add(sid)

    print(f"   Found {len(storage_ids)} unique storage_ids")

    # Create warmup tasks (2 resolutions per image)
    tasks = []
    for sid in storage_ids:
        for res in RESOLUTIONS:
            tasks.append((sid, res))

    total_tasks = len(tasks)
    print(f"\n🔥 Warming up cache: {total_tasks} images ({len(storage_ids)} × {len(RESOLUTIONS)} resolutions)")
    print(f"   Resolutions: {', '.join([r['name'] for r in RESOLUTIONS])}")

    # Download in parallel (2 concurrent requests to avoid overwhelming the server)
    success_count = 0
    error_count = 0
    total_size_mb = 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(warmup_image, sid, res) for sid, res in tasks]

        for i, future in enumerate(as_completed(futures), 1):
            ok, sid, res_name, result = future.result()

            if ok:
                success_count += 1
                size_kb = result
                total_size_mb += size_kb / 1024
                print(f"   [{i}/{total_tasks}] ✅ ID {sid} ({res_name}): {size_kb:.1f} KB")
            else:
                error_count += 1
                print(f"   [{i}/{total_tasks}] ❌ ID {sid} ({res_name}): {result}")

    print("\n" + "=" * 80)
    print(f"✅ CACHE WARMUP COMPLETE")
    print(f"   Success: {success_count}/{total_tasks}")
    print(f"   Errors: {error_count}/{total_tasks}")
    print(f"   Total downloaded: {total_size_mb:.2f} MB")
    print("=" * 80)

if __name__ == '__main__':
    main()
