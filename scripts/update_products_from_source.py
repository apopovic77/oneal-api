#!/usr/bin/env python3
"""Populate derived product information (taxonomy, variants, features) from official O'Neal product pages."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.product_source import fetch_product_source

DATA_FILE = Path(__file__).resolve().parents[1] / "app" / "data" / "products.json"


def update_product(product: dict) -> None:
    meta = product.setdefault("meta", {})
    product_url = meta.get("product_url")
    if not product_url:
        print(f"⚠️  {product.get('id')}: no product_url in metadata, skipping")
        return

    try:
        source = fetch_product_source(product_url, product.get("id"))
    except Exception as exc:  # pragma: no cover - network errors
        print(f"❌ {product.get('id')}: failed to fetch source info ({exc})")
        return

    product["source_url"] = source.source_url

    if source.features:
        product["key_features"] = source.features

    if source.description:
        description = product.get("description") or {}
        description["long"] = source.description
        product["description"] = description

    if source.technical_data:
        product["technical_data"] = [table.model_dump(exclude_none=True) for table in source.technical_data]

    if source.offers:
        product["variants"] = [offer.model_dump(exclude_none=True) for offer in source.offers]

    taxonomy = source.taxonomy
    if taxonomy.sport or taxonomy.product_family or taxonomy.path:
        product["derived_taxonomy"] = taxonomy.model_dump(exclude_none=True)


def main() -> None:
    products = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for product in products:
        update_product(product)
    DATA_FILE.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ Updated {len(products)} products with source information")


if __name__ == "__main__":
    main()
