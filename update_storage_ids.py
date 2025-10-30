#!/usr/bin/env python3
"""
Update storage_ids in products.json from Storage API
"""
import json
import requests

print("Loading products.json...")
with open('app/data/products.json', 'r') as f:
    products = json.load(f)

print(f"Loaded {len(products)} products")

# Get all storage objects with link_ids
print("\nFetching storage objects from API...")
response = requests.get(
    'https://api-storage.arkturian.com/storage/objects?limit=1000',
    headers={'X-API-KEY': 'oneal_demo_token'}
)
storage_objects = response.json().get('items', [])

# Build link_id -> storage_id mapping
link_id_map = {obj['link_id']: obj['id'] for obj in storage_objects if obj.get('link_id')}

print(f"Found {len(link_id_map)} storage objects with link_ids")
print(f"\nProcessing products...")

updated_count = 0
for i, product in enumerate(products):
    if not product.get('media'):
        continue

    for media in product['media']:
        media_id = media.get('id')
        if not media_id:
            continue

        # Check if we have a storage object for this media_id
        if media_id in link_id_map:
            old_id = media.get('storage_id')
            new_id = link_id_map[media_id]
            if old_id != new_id:
                media['storage_id'] = new_id
                updated_count += 1
                if updated_count <= 10:  # Show first 10
                    print(f"  ✓ {media_id} -> storage_id {new_id}")

print(f"\n✅ Updated {updated_count} media items with storage_ids")

# Save updated products
print("\nSaving updated products.json...")
with open('app/data/products.json', 'w') as f:
    json.dump(products, f, indent=2)

print("✅ Done! File saved.")
