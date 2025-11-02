from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ..models.product_source import (
    ProductOffer,
    ProductSourceResponse,
    ProductSourceTaxonomy,
    TechnicalTable,
)


DEFAULT_TIMEOUT = 30.0


SPORT_KEYWORDS = {
    "mountainbike": "mountainbike",
    "mtb": "mountainbike",
    "motocross": "motocross",
    "mx": "motocross",
    "motorcycle": "motocross",
}


FAMILY_KEYWORDS = {
    "helm": "helmet",
    "helmet": "helmet",
    "brille": "goggle",
    "goggl": "goggle",
    "jersey": "jersey",
    "shirt": "jersey",
    "hose": "pants",
    "pant": "pants",
    "short": "shorts",
    "glove": "glove",
    "hand": "glove",
    "protektor": "protector",
    "schuhe": "shoes",
    "stiefel": "boots",
    "boot": "boots",
}


FAMILY_PATH_MAP = {
    "helmet": ["helmets"],
    "goggle": ["goggles"],
    "jersey": ["apparel", "jersey"],
    "pants": ["apparel", "pants"],
    "shorts": ["apparel", "shorts"],
    "glove": ["apparel", "gloves"],
    "protector": ["protectors"],
    "boots": ["boots"],
    "shoes": ["shoes"],
}


@dataclass
class _ExtractionResult:
    html: str
    soup: BeautifulSoup
    schema: Optional[dict]


def _fetch_page(url: str) -> _ExtractionResult:
    with httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    schema_product: Optional[dict] = None
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        # schema could be a dict or a list
        if isinstance(data, dict) and data.get("@type") == "Product":
            schema_product = data
            break
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    schema_product = item
                    break
        if schema_product:
            break

    return _ExtractionResult(html=html, soup=soup, schema=schema_product)


def _extract_offers(schema: Optional[dict], base_url: str) -> Tuple[List[ProductOffer], Optional[float], Optional[str], Optional[str]]:
    offers: List[ProductOffer] = []
    price = None
    currency = None
    availability = None

    if not schema:
        return offers, price, currency, availability

    raw_offers = schema.get("offers", [])
    if isinstance(raw_offers, dict):
        raw_offers = [raw_offers]

    for offer in raw_offers:
        if not isinstance(offer, dict):
            continue
        availability_raw = offer.get("availability")
        if isinstance(availability_raw, str) and availability_raw.startswith("https://schema.org/"):
            availability_clean = availability_raw.rsplit("/", 1)[-1]
        else:
            availability_clean = availability_raw

        offers.append(
            ProductOffer(
                name=offer.get("name"),
                sku=offer.get("sku"),
                gtin13=offer.get("gtin13") or offer.get("gtin"),
                price=offer.get("price"),
                currency=offer.get("priceCurrency"),
                availability=availability_clean,
                url=urljoin(base_url, offer.get("url")) if offer.get("url") else None,
            )
        )

    if offers:
        first_offer = offers[0]
        price = first_offer.price
        currency = first_offer.currency
        availability = first_offer.availability

    return offers, price, currency, availability


def _extract_description_text(soup: BeautifulSoup) -> Tuple[Optional[str], List[str]]:
    container = soup.select_one(
        "[data-product-description], .product__description, .product-single__description, #product-description"
    )
    description = None
    features: List[str] = []

    if not container:
        return description, features

    description = container.get_text(" ", strip=True) or None

    seen = set()
    for li in container.find_all("li"):
        text = li.get_text(" ", strip=True)
        if text and text not in seen:
            features.append(text)
            seen.add(text)

    for p in container.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text and ":" in text and text not in seen:
            features.append(text)
            seen.add(text)

    return description, features


def _extract_technical_tables(soup: BeautifulSoup) -> List[TechnicalTable]:
    tables: List[TechnicalTable] = []
    seen = set()

    for table in soup.select("table"):
        matrix: List[List[str]] = []
        for row in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
            if any(cell for cell in cells):
                matrix.append(cells)

        if not matrix:
            continue

        key = tuple(tuple(row) for row in matrix)
        if key in seen:
            continue
        seen.add(key)

        headers: List[str] = []
        body = matrix
        # If first row looks like a header (text in all cells), treat it as such
        if matrix and all(cell for cell in matrix[0]):
            headers = matrix[0]
            body = matrix[1:]

        tables.append(TechnicalTable(headers=headers, rows=body))

    return tables


def _extract_collections(soup: BeautifulSoup) -> List[str]:
    collections: List[str] = []
    seen = set()
    for link in soup.select('a[href*="/collections/"]'):
        text = link.get_text(strip=True)
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        collections.append(text)
    return collections


def _derive_taxonomy(collections: List[str], schema_category: Optional[str]) -> ProductSourceTaxonomy:
    sport = None
    product_family = None

    for label in collections:
        label_lower = label.lower()
        for keyword, value in SPORT_KEYWORDS.items():
            if keyword in label_lower:
                sport = value
                break
        if sport:
            break

    candidates = []
    if schema_category:
        candidates.append(schema_category)
    candidates.extend(collections)

    for label in candidates:
        if not label:
            continue
        label_lower = label.lower()
        for keyword, value in FAMILY_KEYWORDS.items():
            if keyword in label_lower:
                product_family = value
                break
        if product_family:
            break

    path: List[str] = []
    if sport:
        path.append(sport)
    suffix = FAMILY_PATH_MAP.get(product_family or "")
    if suffix:
        path.extend(suffix)
    elif product_family:
        path.append(product_family)

    return ProductSourceTaxonomy(sport=sport, product_family=product_family, path=path)


def fetch_product_source(product_url: str, product_id: Optional[str] = None) -> ProductSourceResponse:
    extraction = _fetch_page(product_url)
    schema = extraction.schema or {}

    title = None
    if schema.get("name"):
        title = schema.get("name")
    elif extraction.soup.title:
        title = extraction.soup.title.get_text(strip=True)

    offers, price, currency, availability = _extract_offers(schema, product_url)
    description, features = _extract_description_text(extraction.soup)
    technical_data = _extract_technical_tables(extraction.soup)
    collections = _extract_collections(extraction.soup)
    taxonomy = _derive_taxonomy(collections, schema.get("category"))

    brand = schema.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name")

    source_response = ProductSourceResponse(
        source_url=product_url,
        product_id=product_id or schema.get("productID"),
        title=title,
        brand=brand,
        price=price,
        currency=currency,
        availability=availability,
        offers=offers,
        description=description,
        features=features,
        technical_data=technical_data,
        collections=collections,
        taxonomy=taxonomy,
        raw_schema=schema or None,
    )

    return source_response
