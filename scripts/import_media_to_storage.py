#!/usr/bin/env python3
"""
Import O'Neal product images into the Storage API and keep products.json in sync.

This script:
  * optional: cleans the tenant via /storage/admin/clean-tenant
  * fetches Shopify product JSON to obtain all gallery images
  * uploads each image as storage_mode="external" and records returned storage IDs
  * links variant SKUs to their image storage IDs when available
  * writes updated media/variant metadata back into app/data/products.json

Usage:
  python scripts/import_media_to_storage.py [--skip-clean] [--limit N] [--dry-run]

Environment variables:
  STORAGE_API_BASE   (default: https://api-storage.arkturian.com)
  STORAGE_API_KEY    (default: Inetpass1)
  ONEAL_API_BASE     (default: https://oneal-api.arkturian.com/v1)
  ONEAL_API_KEY      (default: oneal_demo_token)
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = ROOT / "app" / "data" / "products.json"

STORAGE_API_BASE = os.getenv("STORAGE_API_BASE", "https://api-storage.arkturian.com")
STORAGE_API_KEY = os.getenv("STORAGE_API_KEY", "oneal_demo_token")
STORAGE_UPLOAD_URL = f"{STORAGE_API_BASE.rstrip('/')}/storage/upload"
STORAGE_CLEAN_URL = f"{STORAGE_API_BASE.rstrip('/')}/storage/admin/clean-tenant"

ONEAL_API_BASE = os.getenv("ONEAL_API_BASE", "https://oneal-api.arkturian.com/v1")
ONEAL_API_KEY = os.getenv("ONEAL_API_KEY", "oneal_demo_token")

DEFAULT_TENANT = "oneal"
USER_AGENT = "oneal-import-script/1.0 (https://arkturian.com)"


def log(msg: str) -> None:
    print(msg, flush=True)


def load_products() -> List[dict]:
    if not PRODUCTS_PATH.exists():
        log(f"❌ products.json not found at {PRODUCTS_PATH}")
        sys.exit(1)
    return json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))


def save_products(products: List[dict]) -> None:
    PRODUCTS_PATH.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clean_tenant(client: httpx.Client, tenant_id: str, batch_size: int = 100, dry_run: bool = False) -> dict:
    payload = {"tenant_id": tenant_id, "batch_size": batch_size, "dry_run": dry_run}
    resp = client.post(
        STORAGE_CLEAN_URL,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()
    log(f"🧹 Clean tenant result: {result}")
    return result


def ensure_shopify_json(url: str, client: httpx.Client) -> Optional[dict]:
    if not url:
        return None
    parsed = urlparse(url)
    slug = parsed.path.rstrip("/").split("/")[-1]
    if not slug:
        return None
    api_url = f"{parsed.scheme}://{parsed.netloc}/products/{slug}.json"
    try:
        resp = client.get(api_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("product")
    except Exception as exc:
        log(f"⚠️  Failed to fetch Shopify JSON for {url}: {exc}")
        return None


def download_image(client: httpx.Client, url: str) -> Tuple[bytes, str]:
    resp = client.get(url, timeout=60)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type") or mimetypes.guess_type(url)[0] or "application/octet-stream"
    return resp.content, content_type


def upload_image_to_storage(
    storage_client: httpx.Client,
    image_bytes: bytes,
    content_type: str,
    filename: str,
    product_id: str,
    title: str,
    external_url: str,
    index: int,
    tenant_id: str,
    collection_id: Optional[str],
) -> Optional[int]:
    files = {
        "file": (filename, image_bytes, content_type),
    }
    ai_context = {
        "product_id": product_id,
        "external_url": external_url,
        "index": index,
        "source": "shopify",
    }
    data = {
        "title": title,
        "description": title,
        "is_public": "true",
        "context": f"product:{product_id}",
        "collection_id": collection_id or product_id,
        "link_id": product_id,
        "storage_mode": "external",
        "external_uri": external_url,
        "ai_context_metadata": json.dumps(ai_context, ensure_ascii=False),
    }
    try:
        resp = storage_client.post(
            STORAGE_UPLOAD_URL,
            headers={"X-API-KEY": STORAGE_API_KEY},
            data=data,
            files=files,
            timeout=120,
        )
        resp.raise_for_status()
        payload = resp.json()
        storage_id = payload.get("id")
        if storage_id is None:
            log(f"⚠️  Upload succeeded but id missing: {payload}")
            return None
        return int(storage_id)
    except httpx.HTTPError as exc:
        log(f"❌ Upload failed for {external_url}: {exc}")
        return None


def build_media_entry(product_id: str, image_data: dict, storage_id: int, index: int) -> dict:
    role = "hero" if index == 0 else "gallery"
    identifier = f"{product_id}-hero" if index == 0 else f"{product_id}-image-{index}"
    alt = image_data.get("alt") or ""
    return {
        "id": identifier,
        "role": role,
        "src": image_data.get("src"),
        "alt": alt,
        "featured": index == 0,
        "width": image_data.get("width"),
        "height": image_data.get("height"),
        "storage_id": storage_id,
        "type": "image",
    }


def normalize_filename(url: str, fallback: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name or fallback
    return name.split("?")[0] or fallback


def process_product(
    product: dict,
    shopify_product: dict,
    storage_client: httpx.Client,
    download_client: httpx.Client,
    uploaded_cache: Dict[str, int],
    tenant_id: str,
) -> Tuple[bool, int]:
    media_updated = False
    images = shopify_product.get("images", []) if shopify_product else []
    if not images:
        return media_updated, 0

    product_id = product["id"]
    new_media: List[dict] = []
    storage_ids_by_image_id: Dict[int, int] = {}

    for position, image in enumerate(images):
        src = image.get("src")
        if not src:
            continue
        storage_id = uploaded_cache.get(src)
        if storage_id is None:
            try:
                image_bytes, content_type = download_image(download_client, src)
            except Exception as exc:
                log(f"❌ Failed to download {src}: {exc}")
                continue
            filename = normalize_filename(src, f"{product_id}-{position+1}.jpg")
            title = f"{product.get('name', product_id)} #{position+1}"
            storage_id = upload_image_to_storage(
                storage_client,
                image_bytes,
                content_type,
                filename,
                product_id,
                title,
                src,
                position,
                tenant_id,
                collection_id=product.get("meta", {}).get("product_url"),
            )
            if storage_id is None:
                continue
            uploaded_cache[src] = storage_id
        storage_ids_by_image_id[image.get("id")] = storage_id
        new_media.append(build_media_entry(product_id, image, storage_id, position))

    if new_media:
        product["media"] = new_media
        media_updated = True

    # Link variants by SKU -> image_id
    if shopify_product:
        shopify_variant_by_sku = {
            variant.get("sku"): variant
            for variant in (shopify_product.get("variants") or [])
            if variant.get("sku")
        }
        for variant in product.get("variants", []):
            sku = variant.get("sku")
            if not sku:
                continue
            shop_variant = shopify_variant_by_sku.get(sku)
            if not shop_variant:
                continue
            image_id = shop_variant.get("image_id")
            if image_id:
                storage_id = storage_ids_by_image_id.get(image_id)
                if storage_id:
                    variant["image_storage_id"] = storage_id
                    variant["image_url"] = next(
                        (img["src"] for img in images if img.get("id") == image_id),
                        None,
                    )
                    media_updated = True

    return media_updated, len(new_media)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import O'Neal product images into storage and update products.json.")
    parser.add_argument("--tenant", default=DEFAULT_TENANT, help="Tenant ID to clean/import (default: oneal)")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for tenant cleanup")
    parser.add_argument("--skip-clean", action="store_true", help="Skip tenant cleanup before import")
    parser.add_argument("--limit", type=int, help="Limit number of products (debug)")
    parser.add_argument("--dry-run", action="store_true", help="Do not upload or modify products.json")
    args = parser.parse_args()

    all_products = load_products()
    total_count = len(all_products)
    if args.limit:
        target_products = all_products[: args.limit]
        log(f"ℹ️  Limiting to first {len(target_products)} of {total_count} products")
    else:
        target_products = all_products
        log(f"ℹ️  Processing {total_count} products")

    headers = {
        "X-API-KEY": STORAGE_API_KEY,
        "X-Tenant-ID": args.tenant,
        "User-Agent": USER_AGENT,
    }

    with httpx.Client(headers=headers) as storage_client, httpx.Client(headers={"User-Agent": USER_AGENT}) as download_client:
        if not args.skip_clean and not args.dry_run:
            clean_tenant(storage_client, tenant_id=args.tenant, batch_size=args.batch_size, dry_run=False)

        uploaded_cache: Dict[str, int] = {}
        updated_count = 0
        total_media = 0

        for idx, product in enumerate(target_products, 1):
            name = product.get("name", product.get("id"))
            product_url = product.get("meta", {}).get("product_url", "")
            shopify_data = ensure_shopify_json(product_url, download_client)
            if not shopify_data:
                log(f"⚠️  No Shopify data for {name}")
                continue

            if args.dry_run:
                log(f"[DRY RUN] Would process {name} ({len(shopify_data.get('images', []))} images)")
                continue

            media_updated, media_count = process_product(
                product,
                shopify_data,
                storage_client,
                download_client,
                uploaded_cache,
                args.tenant,
            )

            if media_updated:
                updated_count += 1
                total_media += media_count
                log(f"✅ Updated media for {name} ({media_count} images)")
            else:
                log(f"ℹ️  No updates for {name}")

    if not args.dry_run:
        save_products(all_products)
        log(f"\n🎉 Completed import: {updated_count} products updated with {total_media} images.")
    else:
        log("\n💡 Dry run finished. No files or products.json were modified.")


if __name__ == "__main__":
    main()
