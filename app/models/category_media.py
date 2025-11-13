from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal


class CategoryMedia(BaseModel):
    """Media asset for a specific category or dimension value"""
    id: str = Field(..., description="Unique identifier")
    dimension: str = Field(..., description="Pivot dimension (e.g., 'category:presentation', 'attribute:product_family')")
    dimensionValue: str = Field(..., description="Dimension value (e.g., 'Helme', 'JERSEYS')")
    mediaType: Literal["image", "video"] = Field(..., description="Type of media asset")
    storageId: int = Field(..., description="Storage Media ID for optimized delivery")
    role: Literal["hero", "background", "thumbnail"] = Field(..., description="Media role/purpose")
    title: Optional[str] = Field(None, description="Display title")
    description: Optional[str] = Field(None, description="Description text")
    priority: Optional[int] = Field(None, description="Sort priority (lower = higher priority)")
    meta: Optional[Dict] = Field(None, description="Additional metadata")


class CategoryMediaCollection(BaseModel):
    """Collection of category media assets"""
    version: str = Field(..., description="Data version")
    description: Optional[str] = Field(None, description="Collection description")
    media: List[CategoryMedia] = Field(..., description="List of media assets")
