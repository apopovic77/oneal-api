#!/usr/bin/env python3
"""
Fix storage_ids in products.json by querying the actual database
"""

import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

PRODUCTS_JSON = Path(__file__).parent.parent / "app/data/products.json"

def get_storage_mapping():
    """Get filename -> storage_id mapping from database"""
    cmd = [
        "ssh", "root@arkturian.com",
        "sqlite3 /var/lib/storage-api/storage.db 'SELECT id, original_filename FROM storage_objects WHERE tenant_id=\"oneal\";'"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    mapping = {}
    for line in result.stdout.strip().split('\n'):
        if '|' in line:
            storage_id, filename = line.split('|', 1)
            mapping[filename] = int(storage_id)

    return mapping

def extract_filename_from_url(url):
    """Extract filename from URL"""
    parsed = urlparse(url)
    # Get the last part of the path (filename)
    filename = parsed.path.split('/')[-1]
    # Remove query parameters for matching
    return filename.split('?')[0]

def main():
    print("=" * 80)
    print("FIXING STORAGE IDS FROM DATABASE")
    print("=" * 80)

    # Get mapping from database
    print("\n📥 Fetching storage mappings from database...")
    storage_mapping = get_storage_mapping()
    print(f"   Found {len(storage_mapping)} storage objects")

    # Load products.json
    print(f"\n📂 Loading {PRODUCTS_JSON}...")
    with open(PRODUCTS_JSON, 'r') as f:
        products = json.load(f)

    # Update storage_ids
    print("\n🔧 Updating storage_ids...")
    updated_count = 0
    missing_count = 0

    for product in products:
        for media in product.get('media', []):
            if not media.get('src'):
                continue

            # Extract filename from URL
            filename = extract_filename_from_url(media['src'])

            # Look up storage_id
            if filename in storage_mapping:
                old_id = media.get('storage_id')
                new_id = storage_mapping[filename]
                media['storage_id'] = new_id

                if old_id != new_id:
                    print(f"   {media['id']}: {old_id} -> {new_id}")
                    updated_count += 1
            else:
                print(f"   ⚠️  Missing: {filename} (media: {media.get('id')})")
                missing_count += 1

    # Save products.json
    print(f"\n💾 Saving {PRODUCTS_JSON}...")
    with open(PRODUCTS_JSON, 'w') as f:
        json.dump(products, f, indent=2)

    print(f"\n✅ Updated {updated_count} storage_ids")
    if missing_count > 0:
        print(f"⚠️  {missing_count} media items not found in storage")

    print("\n" + "=" * 80)
    print("✅ FIX COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
