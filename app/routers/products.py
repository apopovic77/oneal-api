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
import json

router = APIRouter()

# Set to True to return test data instead of real products
TEST_MODE = False  # Use products.json with new OpenAPI-compliant format

DATA_FILE = Path(__file__).resolve().parents[2] / "app" / "data" / "products.json"


def load_products() -> List[Product]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Product(**p) for p in raw]


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
                    # Fallback: Use src URL directly (for demo/test data)
                    # This allows products.json to have direct picsum.photos URLs
                    src_url = str(m.src) if m.src else None
                    media_asset = MediaAsset(
                        link_id=m.id,
                        role=m.role,
                        type="image",  # Assume image for now
                        alt=m.alt or f"{m.role.capitalize()} image",
                        width=800,  # Default for picsum.photos
                        height=800,
                        aspectRatio=1.0,
                        variants=ImageVariants(
                            thumb=src_url,      # Use same URL for all variants
                            preview=src_url,    # In production, storage_client provides different sizes
                            print=src_url,
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
