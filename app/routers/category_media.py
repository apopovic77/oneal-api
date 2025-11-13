"""
Category Media Router

Provides endpoints for category and dimension media assets (hero images, backgrounds, etc.)
"""

from fastapi import APIRouter, Depends, Query
from pathlib import Path
import json
from typing import Optional, List

from ..core.auth import api_key_auth
from ..models.category_media import CategoryMediaCollection, CategoryMedia

router = APIRouter()

# Path to category media data file
DATA_FILE = Path(__file__).resolve().parents[2] / "app" / "data" / "category-media.json"


@router.get("/", response_model=CategoryMediaCollection, dependencies=[Depends(api_key_auth)])
async def get_category_media(
    dimension: Optional[str] = Query(None, description="Filter by dimension (e.g., 'category:presentation')"),
    dimension_value: Optional[str] = Query(None, description="Filter by dimension value (e.g., 'Helme')"),
    role: Optional[str] = Query(None, description="Filter by role (hero, background, thumbnail)")
):
    """
    Get category media assets with optional filtering.

    Returns all media assets or filtered subset based on query parameters.
    """
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Apply filters if provided
    if dimension or dimension_value or role:
        filtered_media = []
        for media in data['media']:
            if dimension and media['dimension'] != dimension:
                continue
            if dimension_value and media['dimensionValue'] != dimension_value:
                continue
            if role and media['role'] != role:
                continue
            filtered_media.append(media)

        data['media'] = filtered_media

    return CategoryMediaCollection(**data)


@router.get("/lookup", response_model=CategoryMedia, dependencies=[Depends(api_key_auth)])
async def lookup_category_media(
    dimension: str = Query(..., description="Dimension (e.g., 'category:presentation')"),
    dimension_value: str = Query(..., description="Dimension value (e.g., 'Helme')")
):
    """
    Lookup a specific media asset by dimension and value.

    Returns 404 if not found.
    """
    from fastapi import HTTPException

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Find matching media
    for media in data['media']:
        if media['dimension'] == dimension and media['dimensionValue'] == dimension_value:
            return CategoryMedia(**media)

    raise HTTPException(
        status_code=404,
        detail=f"No media found for dimension='{dimension}' and dimensionValue='{dimension_value}'"
    )
