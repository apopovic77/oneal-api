from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class Category(BaseModel):
    id: str = Field(..., description="Stable category identifier, e.g. cat:mountainbike/mtb-helme")
    name: str = Field(..., description="Human readable name (label)")
    slug: str = Field(..., description="URL slug of this node (last segment)")
    url: Optional[str] = Field(None, description="Relative URL to the official shop page")
    parent_id: Optional[str] = Field(None, description="Parent category id if any")
    media: Optional[List[str]] = Field(None, description="Optional media URLs associated with the category")


class CategoryListResponse(BaseModel):
    count: int
    results: List[Category]


