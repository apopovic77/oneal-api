"""
Resolved Product Response Models
Product feed with resolved media variants and layout hints
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from .product import ProductAIAnalysis


class ImageVariants(BaseModel):
    """Image variant URLs"""
    thumb: Optional[str] = None
    preview: Optional[str] = None
    print: Optional[str] = None


class VideoVariants(BaseModel):
    """Video variant URLs"""
    hls: Optional[str] = None
    posterThumb: Optional[str] = None
    posterPreview: Optional[str] = None
    print: Optional[str] = None


class MediaAsset(BaseModel):
    """Media asset with resolved variants"""
    link_id: str
    role: str  # hero | detail | lifestyle
    type: str  # image | video
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    aspectRatio: Optional[float] = None
    variants: Optional[ImageVariants] = None
    video: Optional[VideoVariants] = None
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None


class MediaCollection(BaseModel):
    """Collection of media assets grouped by role"""
    hero: Optional[MediaAsset] = None
    detail: List[MediaAsset] = Field(default_factory=list)
    lifestyle: List[MediaAsset] = Field(default_factory=list)


class PriceResolved(BaseModel):
    """Price with formatted string"""
    value: float
    currency: str = "EUR"
    formatted: str  # Pre-formatted like "€399"


class LayoutHints(BaseModel):
    """Layout hints for design templates"""
    recommendedTemplate: str = "card-a4-portrait"
    bleed: Dict[str, float] = {"mm": 3}
    dpi: int = 300
    safeArea: Optional[Dict[str, float]] = {"mm": 5}


class Datasheet(BaseModel):
    """Datasheet/document reference"""
    title: str
    url: str
    type: str = "pdf"


class ProductResolved(BaseModel):
    """Product with resolved media variants"""
    id: str
    sku: Optional[str] = None
    name: str
    brand: Optional[str] = "O'Neal"
    category: List[str]
    season: Optional[int] = None
    status: Optional[str] = "active"
    certifications: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    price: Optional[PriceResolved] = None
    media: MediaCollection = Field(default_factory=MediaCollection)
    datasheets: Optional[List[Datasheet]] = None
    layout: Optional[LayoutHints] = None
    meta: Optional[Dict[str, str]] = None
    ai_tags: Optional[List[str]] = None
    ai_analysis: Optional[ProductAIAnalysis] = None


class ResolvedProductsResponse(BaseModel):
    """Response for resolved products endpoint"""
    count: int
    limit: int = 50
    offset: int = 0
    results: List[ProductResolved]
