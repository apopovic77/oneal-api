#!/usr/bin/env python3
"""
Import CSV products into O'Neal API products.json format

Usage:
    python scripts/import_csv.py /path/to/mtb_products.csv /path/to/mx_products.csv
"""

import csv
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse


def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def parse_price(price_str: str) -> float:
    """Parse price string '9,99' to float 9.99"""
    try:
        # Remove any currency symbols, spaces
        price_str = price_str.replace('€', '').replace(' ', '').strip()
        # Replace comma with dot
        price_str = price_str.replace(',', '.')
        return float(price_str)
    except:
        return 0.0


def extract_category_from_name(name: str) -> List[str]:
    """Try to extract category from product name"""
    categories = []

    name_lower = name.lower()

    # Helmets
    if any(word in name_lower for word in ['helm', 'helmet', 'goggle', 'brille']):
        categories.append('Helmets')

    # Gloves
    if any(word in name_lower for word in ['handschuh', 'glove']):
        categories.append('Gloves')

    # Clothing
    if any(word in name_lower for word in ['jersey', 'hose', 'pants', 'shorts', 'shirt', 'jacke', 'jacket']):
        categories.append('Clothing')

    # Protectors
    if any(word in name_lower for word in ['protektor', 'protector', 'knieschützer', 'knieschutzer', 'ellbogen', 'elbow', 'guard', 'vest']):
        categories.append('Protectors')

    # Accessories
    if any(word in name_lower for word in ['sock', 'socke', 'neckwarmer', 'nackenwarmer', 'sticker', 'tent']):
        categories.append('Accessories')

    # Shoes
    if any(word in name_lower for word in ['schuh', 'shoe']):
        categories.append('Shoes')

    # If no category found, set as "Other"
    if not categories:
        categories.append('Other')

    return categories


def convert_csv_to_product(row: Dict[str, str], product_type: str, index: int) -> Dict[str, Any]:
    """Convert CSV row to O'Neal API product format"""

    name = row.get('Product Name', '').strip()
    price_str = row.get('Price', '0')
    image_url = row.get('Image URL', '').strip()
    product_url = row.get('Product URL', '').strip()

    # Parse price
    price_value = parse_price(price_str)

    # Generate ID
    slug = slugify(name)
    product_id = f"{product_type}-{index:04d}-{slug[:30]}"

    # Extract category
    categories = extract_category_from_name(name)
    categories.append(product_type.upper())  # Add MTB or MX category

    # Extract season from name if present
    season = None
    season_match = re.search(r'20(\d{2})', name)
    if season_match:
        season = 2000 + int(season_match.group(1))

    # Build media item if image URL exists
    media = []
    if image_url:
        media.append({
            "id": f"{product_id}-hero",
            "role": "hero",
            "src": image_url,
            "alt": f"{name} - hero image",
            "featured": True
        })

    # Build product
    product = {
        "id": product_id,
        "sku": None,
        "name": name,
        "brand": "O'Neal",
        "category": categories,
        "season": season,
        "status": "active",
        "description": None,
        "tier": None,
        "series_id": None,
        "series_name": None,
        "key_features": None,
        "certifications": None,
        "materials": None,
        "colors": None,
        "sizes": None,
        "price": {
            "currency": "EUR",
            "value": price_value,
            "formatted": f"€{price_value:.2f}"
        } if price_value > 0 else None,
        "specifications": None,
        "media": media if media else None,
        "datasheets": None,
        "meta": {
            "product_url": product_url,
            "source": product_type
        } if product_url else None
    }

    return product


def main():
    if len(sys.argv) < 3:
        print("Usage: python import_csv.py <mtb_csv> <mx_csv>")
        sys.exit(1)

    mtb_csv = Path(sys.argv[1])
    mx_csv = Path(sys.argv[2])

    if not mtb_csv.exists():
        print(f"Error: MTB CSV not found: {mtb_csv}")
        sys.exit(1)

    if not mx_csv.exists():
        print(f"Error: MX CSV not found: {mx_csv}")
        sys.exit(1)

    print(f"Reading MTB products from: {mtb_csv}")
    print(f"Reading MX products from: {mx_csv}")

    products = []

    # Read MTB products
    with mtb_csv.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            product = convert_csv_to_product(row, 'mtb', idx)
            products.append(product)

    print(f"✓ Loaded {len(products)} MTB products")

    # Read MX products
    mx_start_idx = len(products)
    with mx_csv.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            product = convert_csv_to_product(row, 'mx', idx)
            products.append(product)

    print(f"✓ Loaded {len(products) - mx_start_idx} MX products")
    print(f"✓ Total products: {len(products)}")

    # Write to products.json
    output_file = Path(__file__).parent.parent / "app" / "data" / "products.json"

    with output_file.open('w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully wrote {len(products)} products to: {output_file}")

    # Show sample
    print("\nSample product:")
    print(json.dumps(products[0], indent=2))


if __name__ == "__main__":
    main()
