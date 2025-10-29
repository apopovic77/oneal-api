#!/usr/bin/env python3
"""Enrich products.json with AI analysis from Storage API.

- Reads the base product catalog (default: app/data/products.json)
- For every media.storage_id fetches /storage/objects/{id}
- Extracts AI metadata (colors, materials, use cases, etc.)
- Writes updated JSON (default: app/data/products_enriched.json)
- Can be rerun safely; data is regenerated from Storage API each time

Usage:
    python scripts/enrich_products_with_ai.py \
        --input app/data/products.json \
        --output app/data/products.json

Environment variables:
    STORAGE_API_URL   (default https://api-storage.arkturian.com)
    STORAGE_API_KEY   (default oneal_demo_token)
"""

import argparse
import asyncio
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import httpx

STORAGE_API_URL = os.getenv("STORAGE_API_URL", "https://api-storage.arkturian.com")
STORAGE_API_KEY = os.getenv("STORAGE_API_KEY", "oneal_demo_token")
CONCURRENCY = int(os.getenv("ENRICH_CONCURRENCY", "12"))


@dataclass
class AIAccumulator:
    colors: Set[str] = field(default_factory=set)
    materials: Set[str] = field(default_factory=set)
    visual_harmony_tags: Set[str] = field(default_factory=set)
    keywords: Set[str] = field(default_factory=set)
    use_cases: Set[str] = field(default_factory=set)
    features: Set[str] = field(default_factory=set)
    target_audience: Set[str] = field(default_factory=set)
    emotional_appeal: Set[str] = field(default_factory=set)
    dominant_colors: Set[str] = field(default_factory=set)
    collections: Set[str] = field(default_factory=set)
    style: Optional[str] = None
    layout_notes: Optional[str] = None
    color_palette: Optional[str] = None
    suggested_title: Optional[str] = None
    suggested_subtitle: Optional[str] = None
    ai_tags: Set[str] = field(default_factory=set)

    def merge_product_analysis(self, pa: Dict[str, Any]) -> None:
        if not pa:
            return
        self.colors.update(pa.get("colors", []) or [])
        self.materials.update(pa.get("materials", []) or [])
        self.features.update(pa.get("features", []) or [])
        usage = pa.get("usageContext") or []
        if isinstance(usage, dict):
            usage = usage.values()
        self.use_cases.update(usage)
        target = pa.get("targetAudience") or {}
        if isinstance(target, dict):
            self.target_audience.update(
                [str(v) for v in target.values() if isinstance(v, (str, int, float)) and v]
            )
        if pa.get("style"):
            self.style = pa["style"]

    def merge_visual_analysis(self, va: Dict[str, Any]) -> None:
        if not va:
            return
        color_analysis = va.get("colorAnalysis") or {}
        self.dominant_colors.update(color_analysis.get("dominantColors", []) or [])
        palette = color_analysis.get("colorPalette")
        if palette:
            self.color_palette = palette

    def merge_layout(self, layout: Dict[str, Any]) -> None:
        if not layout:
            return
        self.visual_harmony_tags.update(layout.get("visualHarmonyTags", []) or [])
        note = layout.get("pairingSuggestions")
        if note:
            self.layout_notes = note

    def merge_semantic(self, semantic: Dict[str, Any]) -> None:
        if not semantic:
            return
        self.keywords.update(semantic.get("keywords", []) or [])
        use_cases = semantic.get("useCases") or []
        self.use_cases.update(use_cases)
        ta = semantic.get("targetAudience") or {}
        if isinstance(ta, dict):
            self.target_audience.update(
                [str(v) for v in ta.values() if isinstance(v, (str, int, float)) and v]
            )
        self.emotional_appeal.update(semantic.get("emotionalAppeal", []) or [])

    def merge_media_analysis(self, media: Dict[str, Any]) -> None:
        if not media:
            return
        title = media.get("suggestedTitle") or media.get("suggested_title")
        subtitle = media.get("suggestedSubtitle") or media.get("suggested_subtitle")
        if title:
            self.suggested_title = title
        if subtitle:
            self.suggested_subtitle = subtitle
        self.collections.update(media.get("collectionSuggestions", []) or [])

    def to_payload(self) -> Dict[str, Any]:
        analysis = {
            "colors": sorted(self.colors) or None,
            "materials": sorted(self.materials) or None,
            "visual_harmony_tags": sorted(self.visual_harmony_tags) or None,
            "keywords": sorted(self.keywords) or None,
            "use_cases": sorted(self.use_cases) or None,
            "features": sorted(self.features) or None,
            "target_audience": sorted(self.target_audience) or None,
            "emotional_appeal": sorted(self.emotional_appeal) or None,
            "style": self.style,
            "layout_notes": self.layout_notes,
            "dominant_colors": sorted(self.dominant_colors) or None,
            "color_palette": self.color_palette,
            "suggested_title": self.suggested_title,
            "suggested_subtitle": self.suggested_subtitle,
            "collections": sorted(self.collections) or None,
        }
        # Filter None-only entries
        return {k: v for k, v in analysis.items() if v}

    def ai_tags_payload(self) -> Optional[List[str]]:
        if not self.ai_tags:
            return None
        return sorted(self.ai_tags)


async def fetch_storage_object(client: httpx.AsyncClient, storage_id: int) -> Optional[Dict[str, Any]]:
    url = f"{STORAGE_API_URL}/storage/objects/{storage_id}"
    try:
        response = await client.get(url, headers={"X-API-Key": STORAGE_API_KEY})
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        print(f"[WARN] Storage API {exc.response.status_code} for id={storage_id}")
    except httpx.RequestError as exc:
        print(f"[WARN] Storage API request error for id={storage_id}: {exc}")
    return None


async def enrich_product(client: httpx.AsyncClient, product: Dict[str, Any], cache: Dict[int, Dict[str, Any]]) -> None:
    accumulator = AIAccumulator()
    media_items = product.get("media") or []
    for media in media_items:
        storage_id = media.get("storage_id")
        if not storage_id:
            continue
        if storage_id not in cache:
            cache[storage_id] = await fetch_storage_object(client, storage_id) or {}
        data = cache.get(storage_id) or {}
        if not data:
            continue

        # Flat AI tags on object-level
        tags = data.get("ai_tags") or []
        accumulator.ai_tags.update(tags)

        metadata = data.get("ai_context_metadata") or {}
        extracted = metadata.get("extracted_tags") or {}
        accumulator.colors.update(extracted.get("colors", []) or [])
        accumulator.materials.update(extracted.get("materials", []) or [])
        accumulator.visual_harmony_tags.update(extracted.get("visual_harmony_tags", []) or [])
        accumulator.keywords.update(extracted.get("keywords", []) or [])

        # More detailed sections
        product_analysis = metadata.get("embedding_info", {}).get("metadata", {}).get("product_analysis")
        if not product_analysis:
            product_analysis = metadata.get("product_analysis")
        accumulator.merge_product_analysis(product_analysis or {})

        visual_analysis = metadata.get("embedding_info", {}).get("metadata", {}).get("visual_analysis")
        if not visual_analysis:
            visual_analysis = metadata.get("visual_analysis")
        accumulator.merge_visual_analysis(visual_analysis or {})

        layout_intelligence = metadata.get("layoutIntelligence") or {}
        accumulator.merge_layout(layout_intelligence)

        semantic = metadata.get("semanticProperties") or {}
        accumulator.merge_semantic(semantic)

        media_analysis = metadata.get("mediaAnalysis") or {}
        accumulator.merge_media_analysis(media_analysis)

        # Additional target audience from top-level metadata if present
        embedding_meta = metadata.get("embedding_info", {}).get("metadata", {})
        if embedding_meta.get("style"):
            accumulator.style = embedding_meta["style"]
        accumulator.colors.update(embedding_meta.get("colors", []) or [])

    payload = accumulator.to_payload()
    if payload:
        product["ai_analysis"] = payload
    elif "ai_analysis" in product:
        product.pop("ai_analysis", None)

    ai_tags_payload = accumulator.ai_tags_payload()
    if ai_tags_payload:
        product["ai_tags"] = ai_tags_payload
    elif "ai_tags" in product:
        product.pop("ai_tags", None)


async def process_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    connector_limits = httpx.Limits(max_connections=CONCURRENCY, max_keepalive_connections=CONCURRENCY)
    timeout = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=None)
    cache: Dict[int, Dict[str, Any]] = {}

    async with httpx.AsyncClient(limits=connector_limits, timeout=timeout) as client:
        tasks = [enrich_product(client, product, cache) for product in products]
        await asyncio.gather(*tasks)

    return products


def main():
    parser = argparse.ArgumentParser(description="Enrich O'Neal product catalog with AI metadata")
    parser.add_argument("--input", default="app/data/products.json", help="Input product JSON path")
    parser.add_argument("--output", default=None, help="Output path (default: overwrite input)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    output_path = args.output or args.input

    with open(args.input, "r", encoding="utf-8") as f:
        products = json.load(f)
        if not isinstance(products, list):
            raise ValueError("Input JSON must be a list of products")

    print(f"Loaded {len(products)} products from {args.input}")
    asyncio.run(process_products(products))

    indent = 2 if args.pretty else None
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=indent)
        if indent:
            f.write("\n")

    print(f"Enriched catalog written to {output_path}")


if __name__ == "__main__":
    main()
