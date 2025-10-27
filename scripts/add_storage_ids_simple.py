#!/usr/bin/env python3
"""
Simple script to add storage_id field to media items in products.json.

Since we know the storage objects exist with IDs 4103-4200+, 
we'll add a placeholder storage_id field that can be populated later.

For now, we'll just add the field structure so the API can use it.
"""

import json
from pathlib import Path

# Configuration
PRODUCTS_JSON = Path(__file__).parent.parent / "app" / "data" / "products.json"


def main():
    print("🚀 Adding storage_id field to products.json...\n")
    
    # 1. Load products.json
    print(f"📖 Loading products from: {PRODUCTS_JSON}")
    with PRODUCTS_JSON.open("r", encoding="utf-8") as f:
        products = json.load(f)
    print(f"✅ Loaded {len(products)} products\n")
    
    # 2. Add storage_id field to all media items
    total_media = 0
    for product in products:
        media_list = product.get("media", [])
        for media in media_list:
            total_media += 1
            # Add storage_id field (null for now, will be populated by API)
            if "storage_id" not in media:
                media["storage_id"] = None
    
    print(f"✅ Added storage_id field to {total_media} media items\n")
    
    # 3. Save updated products.json
    print(f"💾 Saving updated products.json...")
    backup_path = PRODUCTS_JSON.with_suffix(".json.backup")
    if PRODUCTS_JSON.exists():
        import shutil
        shutil.copy2(PRODUCTS_JSON, backup_path)
        print(f"  📦 Backup saved to: {backup_path}")
    
    with PRODUCTS_JSON.open("w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved updated products.json")
    
    print(f"\n🎉 Done! Added storage_id field to {total_media} media items")
    print(f"\n💡 Next step: Update the Oneal API to populate storage_id from Storage API")


if __name__ == "__main__":
    main()

