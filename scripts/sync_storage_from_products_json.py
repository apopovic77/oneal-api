#!/usr/bin/env python3
"""
Sync O'Neal products from products.json to Storage API

1. Delete all existing O'Neal storage objects
2. Read products from app/data/products.json
3. Import media to Storage API
4. Update products.json with storage_ids
5. Save products.json

Usage:
    python scripts/sync_storage_from_products_json.py [--dry-run]
"""

import json
import sys
import argparse
import requests
from pathlib import Path

STORAGE_API = "https://api-storage.arkturian.com"
STORAGE_API_KEY = "oneal_demo_token"  # O'Neal tenant API key
ONEAL_TENANT_KEY = "oneal_demo_token"
PRODUCTS_JSON = Path(__file__).parent.parent / "app/data/products.json"

def delete_all_oneal_storage():
    """Delete all storage objects for O'Neal tenant."""
    print("\n🗑️  Deleting all O'Neal storage objects...")

    # Get all O'Neal objects via SQL on server
    # (API endpoint might not have delete-all)
    print("   Note: Run this on server with SQL access:")
    print(f"   DELETE FROM storage_objects WHERE tenant_id='oneal';")
    input("   Press Enter after running SQL delete...")

def import_to_storage(product_id, media_id, media_url, role="hero"):
    """Import a single media item to storage as external reference."""

    print(f"      Registering external URL: {media_url}...")

    # Create minimal 1x1 PNG to satisfy file upload requirement
    import base64
    minimal_png = base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')

    # Upload as external reference
    files = {
        'file': (f"{media_id}.png", minimal_png, 'image/png')
    }
    data = {
        'tenant_id': 'oneal',
        'context': 'oneal_product',
        'collection_id': 'oneal_catalog',
        'link_id': product_id,
        'title': media_id,
        'storage_mode': 'external',
        'external_uri': media_url
    }

    upload_response = requests.post(
        f"{STORAGE_API}/storage/upload",
        files=files,
        data=data,
        headers={'X-API-KEY': STORAGE_API_KEY}
    )
    upload_response.raise_for_status()

    result = upload_response.json()
    storage_id = result.get('id')
    print(f"      ✅ Registered -> storage_id: {storage_id}")
    return storage_id

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--skip-delete', action='store_true', help='Skip deletion step')
    args = parser.parse_args()

    print("=" * 80)
    print("O'NEAL STORAGE SYNC FROM PRODUCTS.JSON")
    print("=" * 80)

    # Step 1: Delete existing
    if not args.skip_delete:
        delete_all_oneal_storage()

    # Step 2: Load products.json
    print(f"\n📂 Loading {PRODUCTS_JSON}...")
    with open(PRODUCTS_JSON, 'r') as f:
        products = json.load(f)
    print(f"   Loaded {len(products)} products")

    # Step 3: Import media and update storage_ids
    print("\n📤 Importing media to storage...")
    updated_count = 0

    for i, product in enumerate(products):
        product_id = product.get('id')
        print(f"\n[{i+1}/{len(products)}] Product: {product_id}")

        if not product.get('media'):
            print(f"   ⏭️  No media")
            continue

        for media in product['media']:
            media_id = media.get('id')
            media_src = media.get('src')
            media_role = media.get('role', 'hero')

            if not media_src:
                print(f"   ⏭️  No src for {media_id}")
                continue

            if args.dry_run:
                print(f"   [DRY RUN] Would import: {media_src}")
                continue

            try:
                storage_id = import_to_storage(product_id, media_id, media_src, media_role)
                media['storage_id'] = storage_id
                updated_count += 1
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

    # Step 4: Save products.json
    if not args.dry_run:
        print(f"\n💾 Saving {PRODUCTS_JSON}...")
        with open(PRODUCTS_JSON, 'w') as f:
            json.dump(products, f, indent=2)
        print(f"   ✅ Saved with {updated_count} storage_ids")
    else:
        print(f"\n[DRY RUN] Would save {updated_count} storage_ids")

    print("\n" + "=" * 80)
    print("✅ SYNC COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
