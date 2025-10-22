#!/usr/bin/env python3
"""
Convert products.json to test_products.py format with realistic images
"""
import json
from pathlib import Path

# Image mapping for different categories
CATEGORY_IMAGES = {
    "Helmets": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w={size}&h={size}&fit=crop",
    "Jerseys": "https://images.unsplash.com/photo-1578932750294-f5075e85f44a?w={size}&h={size}&fit=crop",
    "Gloves": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w={size}&h={size}&fit=crop",
    "Pants": "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w={size}&h={size}&fit=crop",
    "Boots": "https://images.unsplash.com/photo-1542834281-0e5abcbdc5b4?w={size}&h={size}&fit=crop",
    "Shoes": "https://images.unsplash.com/photo-1542834281-0e5abcbdc5b4?w={size}&h={size}&fit=crop",
    "Protectors": "https://images.unsplash.com/photo-1572635148818-ef6fd45eb394?w={size}&h={size}&fit=crop",
    "Goggles": "https://images.unsplash.com/photo-1509695507497-903c140c43b0?w={size}&h={size}&fit=crop",
    "Jackets": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w={size}&h={size}&fit=crop",
    "Bags": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w={size}&h={size}&fit=crop",
}

def get_image_for_category(categories):
    """Get appropriate image URL for product category"""
    for cat in categories:
        if cat in CATEGORY_IMAGES:
            return CATEGORY_IMAGES[cat]
    # Default fallback
    return "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w={size}&h={size}&fit=crop"

def convert_product(product):
    """Convert a product from products.json to resolved format"""
    # Get appropriate image for this category
    image_template = get_image_for_category(product.get("category", []))

    resolved = {
        "id": product["id"],
        "sku": product.get("sku"),
        "name": product["name"],
        "brand": product.get("brand", "O'Neal"),
        "category": product.get("category", []),
        "season": product.get("season", 2026),
        "status": product.get("status", "active"),
        "certifications": product.get("certifications", []),
        "materials": product.get("materials"),
        "colors": product.get("colors", []),
        "sizes": product.get("sizes", []),
        "price": {
            "value": product["price"]["value"],
            "currency": product["price"]["currency"],
            "formatted": f"€{int(product['price']['value']) if float(product['price']['value']).is_integer() else product['price']['value']}"
        },
        "media": {
            "hero": {
                "link_id": f"{product['id']}-hero",
                "role": "hero",
                "type": "image",
                "alt": product["name"],
                "width": 2400,
                "height": 2400,
                "aspectRatio": 1.0,
                "variants": {
                    "thumb": image_template.format(size=200),
                    "preview": image_template.format(size=800),
                    "print": image_template.format(size=2400)
                },
                "video": None,
                "original_filename": f"{product['id']}.jpg",
                "mime_type": "image/jpeg",
                "file_size_bytes": 2457600
            },
            "detail": [],
            "lifestyle": []
        },
        "datasheets": product.get("datasheets"),
        "layout": {
            "recommendedTemplate": "card-a4-portrait",
            "bleed": {"mm": 3},
            "dpi": 300,
            "safeArea": {"mm": 5}
        },
        "meta": {
            "description": f"{product['name']} from O'Neal",
            "last_sync": "2025-10-14T12:00:00Z"
        }
    }
    return resolved

def main():
    # Load products.json
    products_file = Path(__file__).parent / "products.json"
    with open(products_file, 'r') as f:
        products = json.load(f)

    print(f"Converting {len(products)} products...")

    # Convert all products
    resolved_products = [convert_product(p) for p in products]

    # Generate Python file content
    output = '"""\nTest product data for development\n"""\n\n'
    output += 'TEST_PRODUCTS = {\n'
    output += f'    "count": {len(resolved_products)},\n'
    output += '    "results": [\n'

    for i, product in enumerate(resolved_products):
        # Convert to Python dict format
        product_str = json.dumps(product, indent=8)
        # Replace null with None for Python
        product_str = product_str.replace('null', 'None')
        product_str = product_str.replace('true', 'True')
        product_str = product_str.replace('false', 'False')

        output += '        ' + product_str
        if i < len(resolved_products) - 1:
            output += ','
        output += '\n'

    output += '    ]\n'
    output += '}\n'

    # Write to test_products.py
    output_file = Path(__file__).parent / "test_products.py"
    with open(output_file, 'w') as f:
        f.write(output)

    print(f"✅ Generated {output_file} with {len(resolved_products)} products")
    print(f"   Categories covered: {set(cat for p in resolved_products for cat in p['category'])}")

if __name__ == "__main__":
    main()
