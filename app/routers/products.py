from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from ..core.auth import api_key_auth
from ..models.product import Product, ProductListResponse
from ..models.resolved import (
    ResolvedProductsResponse,
    ProductResolved,
    MediaCollection,
    MediaAsset,
    ImageVariants,
    VideoVariants,
    PriceResolved,
    LayoutHints,
)
from ..services.storage_client import storage_client
from ..data.test_products import TEST_PRODUCTS
from pathlib import Path
import hashlib
import json

router = APIRouter()

# Set to True to return test data instead of real products
TEST_MODE = False  # Use products.json with new OpenAPI-compliant format

DATA_FILE = Path(__file__).resolve().parents[2] / "app" / "data" / "products.json"
CAT_FILE = Path(__file__).resolve().parents[2] / "app" / "data" / "kategorien.json"

ROOT_LABEL_BY_SOURCE = {
    "mtb": "Mountainbike",
    "mx": "Motocross",
}

CATEGORY_LABEL_MAP = {
    "mtb": "Mountainbike",
    "mx": "Motocross",
    "helmets": "Helme",
    "clothing": "Kleidung",
    "gloves": "Handschuhe",
    "protectors": "Protektoren",
    "shoes": "Schuhe",
    "accessories": "Accessories",
    "other": "Weitere",
}

ROOT_LABELS = set(ROOT_LABEL_BY_SOURCE.values())

CATEGORY_PATH_OVERRIDES = {
    ("Mountainbike", "Helme"): ["Mountainbike", "Helme"],
    ("Mountainbike", "Kleidung"): ["Mountainbike", "Kleidung"],
    ("Mountainbike", "Handschuhe"): ["Mountainbike", "Kleidung", "Handschuhe"],
    ("Mountainbike", "Protektoren"): ["Mountainbike", "Protektoren"],
    ("Mountainbike", "Schuhe"): ["Mountainbike", "Schuhe"],
    ("Mountainbike", "Accessories"): ["Mountainbike", "Accessories"],
    ("Mountainbike", "Weitere"): ["Mountainbike", "Protektoren", "Weitere"],
    ("Motocross", "Helme"): ["Motocross", "Helme"],
    ("Motocross", "Kleidung"): ["Motocross", "Kleidung"],
    ("Motocross", "Handschuhe"): ["Motocross", "Kleidung", "Handschuhe"],
    ("Motocross", "Protektoren"): ["Motocross", "Protektoren"],
    ("Motocross", "Schuhe"): ["Motocross", "Stiefel"],
    ("Motocross", "Accessories"): ["Motocross", "Accessories"],
    ("Motocross", "Weitere"): ["Motocross", "Protektoren", "Weitere"],
}


def _stable_float(seed: str, min_val: float, max_val: float) -> float:
    """Deterministic pseudo-random float in [min_val, max_val] from a string seed."""
    h = hashlib.md5(seed.encode("utf-8")).hexdigest()
    # Use 8 hex chars -> 32-bit int
    n = int(h[:8], 16)
    r = n / 0xFFFFFFFF
    return min_val + (max_val - min_val) * r


def _normalize_product_dict(p: dict) -> dict:
    """Ensure price and weight exist for test data. Does not mutate input dict."""
    product = dict(p)
    cat_list = product.get("category") or []
    cat0 = (cat_list[0] if isinstance(cat_list, list) and cat_list else "Other").lower()

    # Category-based ranges (rough, for demo data)
    price_ranges = {
        "helmets": (79.0, 449.0),
        "gloves": (9.0, 59.0),
        "clothing": (19.0, 299.0),
        "protectors": (19.0, 199.0),
        "shoes": (49.0, 299.0),
        "boots": (49.0, 299.0),
        "accessories": (5.0, 99.0),
        "other": (10.0, 199.0),
    }
    weight_ranges_g = {
        "helmets": (900.0, 1800.0),
        "gloves": (80.0, 300.0),
        "clothing": (200.0, 1500.0),
        "protectors": (200.0, 1500.0),
        "shoes": (800.0, 2500.0),
        "boots": (800.0, 2500.0),
        "accessories": (20.0, 800.0),
        "other": (100.0, 2000.0),
    }

    # pick range by prefix matching
    def _pick_range(mapping: dict) -> tuple[float, float]:
        for key, rng in mapping.items():
            if key in cat0:
                return rng
        return mapping["other"]

    # Price normalization
    price = product.get("price") or {}
    price_value = price.get("value")
    price_currency = price.get("currency") or "EUR"
    if price_value is None:
        lo, hi = _pick_range(price_ranges)
        # Deterministic: id + category
        seed = f"{product.get('id','')}-{cat0}-price"
        value = round(_stable_float(seed, lo, hi), 2)
        price_value = value
    # formatted string
    symbol = "€" if price_currency.upper() == "EUR" else price_currency
    formatted = f"{symbol}{price_value:.2f}"
    product["price"] = {"currency": price_currency, "value": float(price_value), "formatted": formatted}

    # Weight normalization (grams) in specifications
    specs = dict(product.get("specifications") or {})
    weight = specs.get("weight")
    if weight is None:
        lo, hi = _pick_range(weight_ranges_g)
        seed = f"{product.get('id','')}-{cat0}-weight"
        specs["weight"] = round(_stable_float(seed, lo, hi), 1)
    product["specifications"] = specs

    return product


def _slug_from_url(url: str) -> str:
    s = (url or "").strip("/")
    parts = s.split("/")
    return parts[-1] if parts else s


def _load_category_taxonomy() -> Dict[str, Any]:
    if not CAT_FILE.exists():
        return {"taxonomy": []}
    with CAT_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_category_labels(labels: List[str], source: Optional[str]) -> List[str]:
    normalized: List[str] = []
    root_label: Optional[str] = None
    source_key = (source or "").strip().lower()

    for label in labels or []:
        canonical = CATEGORY_LABEL_MAP.get(label.strip().lower(), label.strip())
        if canonical in ROOT_LABELS:
            root_label = canonical
        normalized.append(canonical)

    if root_label is None and source_key:
        root_label = ROOT_LABEL_BY_SOURCE.get(source_key)

    if not root_label:
        return normalized

    sub_labels = [label for label in normalized if label and label != root_label]

    for sub_label in sub_labels:
        override = CATEGORY_PATH_OVERRIDES.get((root_label, sub_label))
        if override:
            return override

    if sub_labels:
        return [root_label, *sub_labels]

    return [root_label]


def _resolve_category_ids_from_labels(labels: List[str], taxonomy: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    nodes = taxonomy.get("taxonomy", [])
    path_slugs: List[str] = []
    for label in labels:
        match = next((n for n in nodes if (n.get("label") or "").strip().lower() == label.strip().lower()), None)
        if not match:
            break
        slug = _slug_from_url(match.get("url") or match.get("label", "").lower().replace(" ", "-"))
        if slug:
            path_slugs.append(slug)
            ids.append(f"cat:{'/'.join(path_slugs)}")
        nodes = match.get("children", []) or []
    return ids


def load_products() -> List[Product]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    normalized = [_normalize_product_dict(p) for p in raw]
    taxonomy = _load_category_taxonomy()
    enriched: List[Product] = []
    for p in normalized:
        if isinstance(p.get("category"), list) and p.get("category") and not p.get("category_ids"):
            meta = p.get("meta") or {}
            labels = _normalize_category_labels(p["category"], meta.get("source"))
            ids = _resolve_category_ids_from_labels(labels, taxonomy) if labels else []
            if ids:
                p["category"] = labels
                p["category_ids"] = ids
        enriched.append(Product(**p))
    return enriched


async def to_resolved(products: List[Product]) -> List[ProductResolved]:
    """
    Convert products to resolved format with resolved media variants.
    Makes a single batch call to Storage API to resolve all media assets.
    """
    # Step 1: Collect all link_ids from all products
    queries = []
    for p in products:
        if p.media:
            for m in p.media:
                queries.append({"link_id": m.id, "role": m.role})

    # Step 2: Batch resolve all media variants from Storage API
    variants_map = {}
    if queries:
        variants_map = await storage_client.get_variants_batch(queries)

    # Step 3: Build ProductFigmaV2 for each product
    results = []
    for p in products:
        # Build price
        price_resolved = None
        if p.price and p.price.value is not None:
            symbol = "€" if (p.price.currency or "EUR").upper() == "EUR" else p.price.currency
            formatted = f"{symbol}{int(p.price.value) if p.price.value.is_integer() else p.price.value}"
            price_resolved = PriceResolved(
                value=p.price.value,
                currency=p.price.currency or "EUR",
                formatted=formatted
            )

        # Build media collection
        media_collection = MediaCollection()
        if p.media:
            for m in p.media:
                # CHANGED: Use src URL directly from product.media instead of storage_client
                # For demo/test products with picsum.photos or direct URLs
                asset_data = variants_map.get(m.id)

                # If storage_client has data, use it (production mode)
                if asset_data:
                    # Build variants from storage_client
                    variants = None
                    video = None
                    if asset_data.get("type") == "image":
                        variants = ImageVariants(
                            thumb=asset_data.get("variants", {}).get("thumb"),
                            preview=asset_data.get("variants", {}).get("preview"),
                            print=asset_data.get("variants", {}).get("print"),
                        )
                    elif asset_data.get("type") == "video":
                        video = VideoVariants(
                            hls=asset_data.get("video", {}).get("hls"),
                            posterThumb=asset_data.get("video", {}).get("posterThumb"),
                            posterPreview=asset_data.get("video", {}).get("posterPreview"),
                            print=asset_data.get("video", {}).get("print"),
                        )

                    media_asset = MediaAsset(
                        link_id=m.id,
                        role=m.role,
                        type=asset_data.get("type", "image"),
                        alt=m.alt,
                        width=asset_data.get("width"),
                        height=asset_data.get("height"),
                        aspectRatio=asset_data.get("aspectRatio"),
                        variants=variants,
                        video=video,
                        original_filename=asset_data.get("original_filename"),
                        mime_type=asset_data.get("mime_type"),
                        file_size_bytes=asset_data.get("file_size_bytes"),
                    )
                else:
                    # Fallback: Use Storage API proxy for ALL images (with or without storage_id)
                    # This enables transformation, caching, and optimization for all external URLs
                    src_url = str(m.src) if m.src else None
                    storage_id = getattr(m, 'storage_id', None)
                    
                    if storage_id:
                        # Option 1: Real storage object - use direct media endpoint
                        base_url = f"https://api-storage.arkturian.com/storage/media/{storage_id}"
                        thumb_url = f"{base_url}?width=400&format=webp&quality=80"
                        preview_url = f"{base_url}?width=800&format=webp&quality=85"
                        print_url = f"{base_url}?width=2000&format=jpg&quality=95"
                    elif src_url:
                        # Option 2: External URL - use Storage API proxy endpoint
                        # This creates a virtual storage object that proxies the external URL
                        # The Storage API will cache and transform the image on-the-fly
                        import urllib.parse
                        encoded_url = urllib.parse.quote(src_url, safe='')
                        base_url = f"https://api-storage.arkturian.com/storage/proxy"
                        thumb_url = f"{base_url}?url={encoded_url}&width=400&format=webp&quality=80"
                        preview_url = f"{base_url}?url={encoded_url}&width=800&format=webp&quality=85"
                        print_url = f"{base_url}?url={encoded_url}&width=2000&format=jpg&quality=95"
                    else:
                        # No image available
                        thumb_url = None
                        preview_url = None
                        print_url = None
                    
                    media_asset = MediaAsset(
                        link_id=m.id,
                        role=m.role,
                        type="image",  # Assume image for now
                        alt=m.alt or f"{m.role.capitalize()} image",
                        width=800,  # Default for picsum.photos
                        height=800,
                        aspectRatio=1.0,
                        variants=ImageVariants(
                            thumb=thumb_url,
                            preview=preview_url,
                            print=print_url,
                        ),
                        video=None,
                        original_filename=None,
                        mime_type="image/jpeg",
                        file_size_bytes=None,
                    )

                # Add to appropriate collection
                if m.role == "hero":
                    media_collection.hero = media_asset
                elif m.role == "detail":
                    media_collection.detail.append(media_asset)
                elif m.role == "lifestyle":
                    media_collection.lifestyle.append(media_asset)

        # Build ProductResolved
        product_resolved = ProductResolved(
            id=p.id,
            sku=p.sku,
            name=p.name,
            brand=p.brand,
            category=p.category,
            season=p.season,
            status=p.status,
            certifications=p.certifications,
            materials=p.materials,
            colors=p.colors,
            sizes=p.sizes,
            price=price_resolved,
            media=media_collection,
            layout=LayoutHints(),  # Use defaults
            meta=p.meta,
            ai_tags=p.ai_tags,
            ai_analysis=p.ai_analysis,
        )
        results.append(product_resolved)

    return results


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    search: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    season: Optional[int] = Query(default=None),
    cert: Optional[str] = Query(default=None),
    price_min: Optional[float] = Query(default=None),
    price_max: Optional[float] = Query(default=None),
    sort: Optional[str] = Query(default=None, pattern="^(name|price|season)$"),
    order: Optional[str] = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=100000),
    offset: int = Query(default=0, ge=0),
    format: Optional[str] = Query(default=None),
    _: None = Depends(api_key_auth),
):
    # If in test mode and resolved format requested, return test data directly
    if TEST_MODE and format == "resolved":
        all_results = TEST_PRODUCTS["results"]
        page = all_results[offset : offset + limit]
        results_resolved = [ProductResolved(**r) for r in page]
        response = ResolvedProductsResponse(
            count=TEST_PRODUCTS["count"],
            limit=limit,
            offset=offset,
            results=results_resolved
        )
        return JSONResponse(content=response.model_dump())

    products = load_products()

    # filtering
    def matches(p: Product) -> bool:
        if search:
            s = search.lower()
            hay: List[str] = [p.name or "", p.id or "", (p.sku or ""), " ".join(p.category or [])]
            if not any(s in h.lower() for h in hay):
                return False
        if category and (not p.category or category not in p.category):
            return False
        if season is not None and p.season != season:
            return False
        if cert and (not p.certifications or cert not in p.certifications):
            return False
        if price_min is not None:
            if not p.price or p.price.value is None or p.price.value < price_min:
                return False
        if price_max is not None:
            if not p.price or p.price.value is None or p.price.value > price_max:
                return False
        return True

    filtered = [p for p in products if matches(p)]

    # sorting
    if sort:
        reverse = order == "desc"
        if sort == "name":
            filtered.sort(key=lambda p: (p.name or "").lower(), reverse=reverse)
        elif sort == "season":
            filtered.sort(key=lambda p: (p.season or -1), reverse=reverse)
        elif sort == "price":
            filtered.sort(key=lambda p: (p.price.value if p.price else float("inf")), reverse=reverse)

    count = len(filtered)
    page = filtered[offset : offset + limit]

    if format == "resolved":
        results_resolved = await to_resolved(page)
        response = ResolvedProductsResponse(
            count=count,
            limit=limit,
            offset=offset,
            results=results_resolved
        )
        return JSONResponse(content=response.model_dump())

    return {"count": count, "results": page}


@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, _: None = Depends(api_key_auth)):
    products = load_products()
    product = next((p for p in products if p.id == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
