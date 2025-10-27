from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Literal
from enum import Enum


class Price(BaseModel):
    currency: str = "EUR"
    value: float
    formatted: str = Field(..., description="Formatted price string (e.g. '€399.00')")


class MediaItem(BaseModel):
    id: str
    role: Literal["hero", "detail", "lifestyle", "action", "studio"] = Field(..., description="Image role/purpose")
    src: HttpUrl
    alt: Optional[str] = None
    caption: Optional[str] = Field(None, description="Image caption for catalog")
    featured: bool = Field(False, description="Featured/highlight image")
    storage_id: Optional[int] = Field(None, description="Storage API object ID for optimized image delivery")


class Datasheet(BaseModel):
    title: str
    url: HttpUrl
    type: Optional[str] = "pdf"


class ProductDescription(BaseModel):
    short: Optional[str] = Field(None, description="Short description for product grids (1-2 sentences)")
    long: Optional[str] = Field(None, description="Full description for detail pages (multiple paragraphs)")


class ProductSpecifications(BaseModel):
    weight: Optional[float] = Field(None, description="Weight in grams")
    dimensions: Optional[str] = Field(None, description="Dimensions (L×W×H)")
    shell_material: Optional[str] = None
    liner_material: Optional[str] = None


class Product(BaseModel):
    id: str
    sku: Optional[str] = None
    name: str
    brand: Optional[str] = "O'Neal"
    category: List[str]
    season: Optional[int] = None
    status: Optional[str] = Field("active", description="active | draft | archived")
    description: Optional[ProductDescription] = None
    tier: Optional[Literal["entry", "mid", "premium"]] = Field(None, description="Product quality tier")
    series_id: Optional[str] = Field(None, description="Series/family identifier for grouping related products")
    series_name: Optional[str] = Field(None, description="Display name for product series")
    key_features: Optional[List[str]] = Field(None, description="Highlighted features for catalog")
    certifications: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    price: Optional[Price] = None
    specifications: Optional[ProductSpecifications] = None
    media: Optional[List[MediaItem]] = None
    datasheets: Optional[List[Datasheet]] = None
    meta: Optional[Dict[str, str]] = Field(None, description="Additional unstructured metadata")


class ProductListResponse(BaseModel):
    count: int
    results: List[Product]


class FigmaFeedItem(BaseModel):
    id: str
    name: Optional[str] = None
    price: Optional[str] = None
    image: Optional[HttpUrl] = None
    category: Optional[str] = None
    season: Optional[str] = None
    cert: Optional[str] = None
