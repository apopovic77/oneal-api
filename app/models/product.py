from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict


class Price(BaseModel):
    currency: str = "EUR"
    value: float


class MediaItem(BaseModel):
    id: str
    role: str = Field(..., description="hero | detail | lifestyle")
    src: HttpUrl
    alt: Optional[str] = None


class Datasheet(BaseModel):
    title: str
    url: HttpUrl
    type: Optional[str] = "pdf"


class Product(BaseModel):
    id: str
    sku: Optional[str] = None
    name: str
    brand: Optional[str] = "O’Neal"
    category: List[str]
    season: Optional[int] = None
    status: Optional[str] = Field("active", description="active | draft | archived")
    certifications: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    price: Optional[Price] = None
    media: Optional[List[MediaItem]] = None
    datasheets: Optional[List[Datasheet]] = None
    meta: Optional[Dict[str, str]] = None


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
