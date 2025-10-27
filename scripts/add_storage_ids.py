#!/usr/bin/env python3
"""
Add storage_id to products.json media items.

This script uses the MCP O'Neal Storage API to fetch storage objects
and match them with products in products.json.

Since we can't directly call MCP from Python, this script will:
1. Load products.json
2. Print commands to manually fetch storage IDs
3. You can then manually update the JSON or use the MCP tools
"""

import json
from pathlib import Path
from typing import Dict, List

# Configuration
PRODUCTS_JSON = Path(__file__).parent.parent / "app" / "data" / "products.json"

# Simulated storage objects (you'll need to fetch these via MCP)
# For now, we'll use a simple mapping based on context patterns
STORAGE_OBJECTS = []


def build_context_mapping(storage_objects: List[Dict]) -> Dict[str, int]:
    """Build mapping from context to storage_id."""
    print("\n🗺️  Building context → storage_id mapping...")
    
    mapping = {}
    for obj in storage_objects:
        context = obj.get("context")
        storage_id = obj.get("id")
        
        if context and storage_id:
            # Context format: "oneal_product_{product_id}"
            # We want to map product_id to storage_id
            if context.startswith("oneal_product_"):
                product_context = context.replace("oneal_product_", "")
                mapping[product_context] = storage_id
                
                # Also map the full context
                mapping[context] = storage_id
    
    print(f"✅ Built mapping with {len(mapping)} entries")
    return mapping


def add_storage_ids_to_products(products: List[Dict], mapping: Dict[str, int]) -> tuple[int, int]:
    """Add storage_id to media items in products."""
    print("\n📝 Adding storage_ids to products...")
    
    total_media = 0
    matched_media = 0
    
    for product in products:
        product_id = product.get("id")
        media_list = product.get("media", [])
        
        for media in media_list:
            total_media += 1
            media_id = media.get("id")
            
            # Try to find storage_id by matching context
            # Context could be: product_id, media_id, or oneal_product_{product_id}
            storage_id = None
            
            # Try different matching strategies
            if media_id:
                # Try exact media_id match
                storage_id = mapping.get(media_id)
                
                if not storage_id:
                    # Try product_id match
                    storage_id = mapping.get(product_id)
                
                if not storage_id:
                    # Try with oneal_product_ prefix
                    storage_id = mapping.get(f"oneal_product_{product_id}")
                
                if not storage_id:
                    # Try with oneal_product_ prefix on media_id
                    storage_id = mapping.get(f"oneal_product_{media_id}")
            
            if storage_id:
                media["storage_id"] = storage_id
                matched_media += 1
            else:
                print(f"  ⚠️  No storage match for: {product_id} / {media_id}")
    
    print(f"✅ Matched {matched_media}/{total_media} media items ({matched_media/total_media*100:.1f}%)")
    return total_media, matched_media


def main():
    print("🚀 Starting storage_id addition process...\n")
    
    # 1. Load products.json
    print(f"📖 Loading products from: {PRODUCTS_JSON}")
    with PRODUCTS_JSON.open("r", encoding="utf-8") as f:
        products = json.load(f)
    print(f"✅ Loaded {len(products)} products\n")
    
    # 2. Fetch all storage objects
    storage_objects = fetch_all_storage_objects()
    
    # 3. Build context mapping
    mapping = build_context_mapping(storage_objects)
    
    # 4. Add storage_ids to products
    total, matched = add_storage_ids_to_products(products, mapping)
    
    # 5. Save updated products.json
    print(f"\n💾 Saving updated products.json...")
    backup_path = PRODUCTS_JSON.with_suffix(".json.backup")
    if PRODUCTS_JSON.exists():
        PRODUCTS_JSON.rename(backup_path)
        print(f"  📦 Backup saved to: {backup_path}")
    
    with PRODUCTS_JSON.open("w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved updated products.json")
    
    print(f"\n🎉 Done! Added storage_id to {matched}/{total} media items")


if __name__ == "__main__":
    main()

