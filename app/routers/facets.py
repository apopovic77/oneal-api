from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from ..core.auth import api_key_auth
from ..models.product import Product
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


@router.get("/facets")
async def get_facets(_: None = Depends(api_key_auth)) -> Dict[str, Any]:
    products = load_products()
    categories = set()
    seasons = set()
    certs = set()
    min_price = None
    max_price = None

    for p in products:
        for c in p.category or []:
            categories.add(c)
        if p.season is not None:
            seasons.add(p.season)
        for ce in p.certifications or []:
            certs.add(ce)
        if p.price and p.price.value is not None:
            v = p.price.value
            min_price = v if min_price is None or v < min_price else min_price
            max_price = v if max_price is None or v > max_price else max_price

    return {
        "category": sorted(categories),
        "season": sorted(seasons),
        "certification": sorted(certs),
        "priceRange": {"min": min_price or 0, "max": max_price or 0},
    }
