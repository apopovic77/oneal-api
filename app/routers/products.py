from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from ..core.auth import api_key_auth
from ..models.product import Product, ProductListResponse, FigmaFeedItem
from pathlib import Path
import json

router = APIRouter()

DATA_FILE = Path(__file__).resolve().parents[2] / "app" / "data" / "products.json"


def load_products() -> List[Product]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Product(**p) for p in raw]


def to_figma_feed(products: List[Product]) -> List[FigmaFeedItem]:
    items: List[FigmaFeedItem] = []
    for p in products:
        price_str = None
        if p.price and p.price.value is not None:
            symbol = "€" if (p.price.currency or "").upper() == "EUR" else p.price.currency
            price_str = f"{symbol}{int(p.price.value) if p.price.value.is_integer() else p.price.value}"
        image = None
        if p.media:
            hero = next((m for m in p.media if m.role == "hero"), None)
            image = hero.src if hero else None
        cert = None
        if p.certifications:
            cert = " / ".join(sorted(p.certifications))
        items.append(
            FigmaFeedItem(
                id=p.id,
                name=p.name,
                price=price_str,
                image=image,
                category=p.category[0] if p.category else None,
                season=str(p.season) if p.season is not None else None,
                cert=cert,
            )
        )
    return items


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
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    format: Optional[str] = Query(default=None),
    _: None = Depends(api_key_auth),
):
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

    if format == "figma-feed":
        return {"count": count, "results": to_figma_feed(page)}  # type: ignore

    return {"count": count, "results": page}


@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, _: None = Depends(api_key_auth)):
    products = load_products()
    product = next((p for p in products if p.id == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
