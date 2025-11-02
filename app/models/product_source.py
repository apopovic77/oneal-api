from typing import List, Optional
from pydantic import BaseModel, Field


class ProductOffer(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    gtin13: Optional[str] = Field(None, description="GTIN/EAN code")
    price: Optional[float] = None
    currency: Optional[str] = None
    availability: Optional[str] = None
    url: Optional[str] = None


class TechnicalTable(BaseModel):
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)


class ProductSourceTaxonomy(BaseModel):
    sport: Optional[str] = None
    product_family: Optional[str] = None
    path: List[str] = Field(default_factory=list, description="Normalized taxonomy path (e.g. ['mountainbike', 'apparel', 'jersey'])")


class ProductSourceResponse(BaseModel):
    source_url: str
    product_id: Optional[str] = None
    title: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    availability: Optional[str] = None
    offers: List[ProductOffer] = Field(default_factory=list)
    description: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    technical_data: List[TechnicalTable] = Field(default_factory=list)
    collections: List[str] = Field(default_factory=list)
    taxonomy: ProductSourceTaxonomy = Field(default_factory=ProductSourceTaxonomy)
    raw_schema: Optional[dict] = Field(None, description="Raw schema.org Product JSON extracted from the page")
