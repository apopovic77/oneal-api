from fastapi import APIRouter
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
from ..models.category import Category, CategoryListResponse


router = APIRouter()

DATA_FILE = Path(__file__).resolve().parents[2] / "app" / "data" / "kategorien.json"


def _slug_from_url(url: str) -> str:
    if not url:
        return ""
    s = url.strip("/")
    parts = s.split("/")
    return parts[-1] if parts else s


def _assign_ids(node: Dict[str, Any], parent_id: Optional[str], path_slugs: List[str], out: List[Category]):
    slug = _slug_from_url(node.get("url") or node.get("label", "").lower().replace(" ", "-"))
    current_path = path_slugs + ([slug] if slug else [])
    cat_id = f"cat:{'/'.join([p for p in current_path if p])}"
    cat = Category(
        id=cat_id,
        name=node.get("label", ""),
        slug=slug,
        url=node.get("url"),
        parent_id=parent_id,
        media=None,
    )
    out.append(cat)
    for child in node.get("children", []) or []:
        _assign_ids(child, cat_id, current_path, out)


def _load_categories() -> List[Category]:
    if not DATA_FILE.exists():
        return []
    raw = json.loads(DATA_FILE.read_text("utf-8"))
    results: List[Category] = []
    for root in raw.get("taxonomy", []):
        _assign_ids(root, None, [], results)
    return results


@router.get("/categories", response_model=CategoryListResponse)
def list_categories():
    cats = _load_categories()
    return CategoryListResponse(count=len(cats), results=cats)


