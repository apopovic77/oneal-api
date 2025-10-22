# O’Neal Product Config Tool + Figma Integration — Functional & Technical Spec (v1)

## 1) Executive Summary
Build a product configuration UI and a companion Figma plugin that consume the existing O’Neal Product API, render low-res assets during design, and automatically swap to high-res assets for print-quality PDF export. Media is hosted on a dedicated media server that can dynamically deliver multiple sizes/qualities via URL parameters.

Outcomes:
- Comfortable UI for browsing/filtering products and assembling print layouts.
- Figma plugin to place product cards/tiles/sheets with live API data and media.
- Low-res in design mode, automatic high-res swap before export.
- Clear contracts: figma-feed v2 endpoint and media URL schema.

Non-goals:
- No persistence of custom layouts server-side (v1: client-side only; optional export/import JSON manifest).
- No write operations to the product API (read-only v1).

## 2) Actors & Workflows
### Actors
- Marketing/Designers: compose pages with products inside Figma.
- Dev/Automation: integrate the product feed and media server.

### Primary Workflows
1. Discover products: filter/search in the Config Tool UI using `category`, `season`, `cert`, price range.
2. Select products: curate a set, choose image roles (hero/detail/lifestyle), and generate a Manifest.
3. Place in Figma: plugin imports Manifest, creates print-ready frames/cards using templates.
4. Design mode: plugin ensures all images use low-res variants for snappy editing.
5. Export to PDF: plugin runs “Prepare for Print”, swaps all images to high-res, exports PDF, then restores low-res.

## 3) System Architecture
- O’Neal Product API (FastAPI, read-only). New v2 feed endpoint for Figma with media variants.
- Media Server (external): delivers images by URL parameters (width/height/fit/format/quality/dpr/mode).
- Product Config Tool (Web UI): reads API, builds selection, outputs Manifest JSON.
- Figma Plugin: reads Manifest and/or calls API directly; places frames; handles quality swap + export.

Communication:
- Config Tool → Product API (`/v1/products`, `/v1/facets`, `/v1/figma-feed` v2 minimal, only pointers like link_id/role).
- Figma Plugin → Storage API `/storage/asset-refs` to resolve variants (thumb/preview/print) by `link_id` and `role`.
- Config Tool → Figma Plugin (via paste/upload Manifest JSON) containing pointer(s), not concrete variant URLs.

## 4) Data Contracts
### 4.1 Figma-Feed v2 (new)
Add a new endpoint `GET /v1/figma-feed` returning minimal, pointer-based items. Media variants are resolved by the Storage API.

Query params (subset mirrors `/v1/products`):
- `search, category, season, cert, price_min, price_max, sort, order, limit, offset`.

Response (JSON):
```json
{
  "count": 123,
  "results": [
    {
      "id": "prd_helmet_123",
      "name": "O’Neal Helmet Alpha",
      "price": {
        "value": 199.99,
        "currency": "EUR",
        "pretty": "€199.99"
      },
      "category": ["Helmets"],
      "season": 2026,
      "cert": "DOT / ECE", 
      "mediaPointers": {
        "hero": { "link_id": "prd_helmet_123", "role": "hero", "alt": "Front view helmet", "storageId": 81 },
        "detail": [ { "link_id": "prd_helmet_123", "role": "detail", "alt": "Side detail", "storageId": 82 } ]
      },
      "datasheets": [
        { "title": "Datasheet", "url": "https://media.example.com/ds/helmet123.pdf" }
      ],
      "layout": {
        "recommendedTemplate": "card-a4-portrait",
        "bleed": { "mm": 3 },
        "dpi": 300
      }
    }
  ]
}
```

Notes:
- Product API provides only pointers: `link_id` (group) and optional `role`. Optionally include `storageId` to pin a specific asset.
- Plugin calls Storage: `/storage/asset-refs?link_id=...&role=hero` or `/storage/asset-refs?object_id={storageId}`.
- `price.pretty` is preformatted for UI; `price.value/currency` are raw.
- `layout` hints help plugin pick a default frame/template.

### 4.2 Storage Variant Resolution
Use Storage endpoint:

`GET https://api.arkturian.com/storage/asset-refs?link_id=PRD123&role=hero`

Response (image):
```json
{
  "count": 1,
  "results": [
    {
      "id": 81,
      "type": "image",
      "role": "hero",
      "variants": {
        "thumb": "https://.../thumbnails/thumb_u1_....jpg?v=...",
        "preview": "https://vod.arkturian.com/webview/web_u1_....jpg?v=...",
        "print": "https://.../uploads/storage/media/u1_....jpg?v=..."
      },
      "width": 2048,
      "height": 1536,
      "link_id": "PRD123"
    }
  ]
}
```

Response (video):
```json
{
  "count": 1,
  "results": [
    {
      "id": 82,
      "type": "video",
      "role": "lifestyle",
      "video": {
        "hls": "https://vod.arkturian.com/media/u1_.../master.m3u8",
        "posterThumb": "https://.../thumbnails/thumb_u1_....jpg?v=...",
        "posterPreview": "https://vod.arkturian.com/webview/web_u1_....jpg?v=...",
        "print": "https://.../uploads/storage/media/u1_....mp4?v=..."
      },
      "width": 1920,
      "height": 1080,
      "duration": 20.1,
      "link_id": "PRD123"
    }
  ]
}
```

### 4.3 Media Server URL Schema (recommendation)
Base: `https://media.example.com/{path/to/asset}`

Parameters:
- `w`/`h`: target width/height in px
- `fit`: `cover | contain | inside | outside`
- `fm`: `webp | jpg | png`
- `q`: quality 1–100
- `dpr`: device pixel ratio (1 | 2)
- `bg`: background color for flattening
- `mode`: `preview | print` (semantic flag for logging/CDN routing)
- Optional `sig` or token for signed URLs if needed

Examples:
- Design (snappy): `...w=1024&h=1024&fit=cover&fm=webp&q=70&mode=preview`
- Print (hi-res): `...w=3508&h=2480&fit=inside&fm=png&q=95&mode=print` (≈ A4 @ 300dpi)

Additionally, for direct image serving with minimal roundtrips (performance):

`GET https://api.arkturian.com/storage/media/{object_id}?variant=medium&display_for=figma-feed`

- Returns the image binary; generates and persists the derivative on first request.
- Alternatives: `variant=thumbnail|full` or specify `width,height,format,quality`.

### 4.4 Manifest JSON (Config Tool → Figma Plugin)
```json
{
  "version": 1,
  "generatedAt": "2025-10-13T10:00:00Z",
  "source": {
    "apiBase": "http://localhost:8000/v1",
    "filters": { "category": "Helmets", "season": 2026 }
  },
  "products": [
    {
      "id": "prd_helmet_123",
      "name": "O’Neal Helmet Alpha",
      "price": { "pretty": "€199.99" },
      "category": ["Helmets"],
      "season": 2026,
      "cert": "DOT / ECE",
      "mediaPointers": {
        "hero": { "link_id": "PRD123", "role": "hero", "alt": "Front view helmet", "storageId": 81 }
      },
      "template": "card-a4-portrait"
    }
  ]
}
```

## 5) Product Config Tool (Web UI)
### Features
- Filters: category, season, certification, price range (backed by `/v1/facets`).
- Search-as-you-type; sort by name/price/season.
- Product card with selectable media roles (choose hero, add details).
- Build Manifest: selected products + chosen media → downloadable JSON.
- Preview Figma card layout with low-res URLs.

### Tech
- SPA (React/Vue/Svelte), fetch from existing API endpoints.
- Store selection and preferences in local storage.
- Optional: import/export manifests to share sets across designers.

## 6) Figma Plugin Design
### Commands
- “Import Manifest” → parse JSON, validate schema, store in plugin data.
- “Place Product Cards” → create frames based on template per product.
- “Toggle Quality” → preview vs print, swapping image URLs for fills.
- “Prepare for Print & Export PDF” → swap to print, export, swap back to preview.

### Templates (internal)
- `card-a4-portrait`, `card-a4-landscape`, `tile-square` (baseline set).
- Auto Layout for consistent spacing; text styles for headings/body/price.
- Variables for brand colors and padding; safe-area + bleed guides.

### Node Structure (example)
- Frame (A4 Portrait)
  - Image (hero) — fill from URL
  - Text (name)
  - Text (price)
  - Text (cert)
  - Repeater of detail images (optional)

### Quality Swap Strategy
- Each image node stores both URLs in plugin data: `{ previewUrl, printUrl }`.
- Toggle command rewrites fills to `previewUrl` or `printUrl`.
- Export command wraps Figma’s `exportAsync({ format: 'PDF' })` after switching to print.

### Caching & Performance
- Cache feed responses with ETag/If-None-Match where possible.
- Defer image loading until placement; use preview first to keep UI responsive.

### Error Handling
- Missing assets → show placeholder and collect a report.
- URL unreachable → retry with backoff; surface actionable message.

## 7) API Additions & OpenAPI
Add `GET /v1/figma-feed` with schema below. Maintain current endpoints intact.

```yaml
openapi: 3.1.0
info: { title: O’Neal Product API, version: "1.1" }
paths:
  /figma-feed:
    get:
      security: [{ apiKeyAuth: [] }]
      summary: Figma-oriented product feed with media variants
      parameters:
        - in: query
          name: search
          schema: { type: string }
        - in: query
          name: category
          schema: { type: string }
        - in: query
          name: season
          schema: { type: integer }
        - in: query
          name: cert
          schema: { type: string }
        - in: query
          name: price_min
          schema: { type: number }
        - in: query
          name: price_max
          schema: { type: number }
        - in: query
          name: sort
          schema: { type: string, enum: [name, price, season] }
        - in: query
          name: order
          schema: { type: string, enum: [asc, desc], default: asc }
        - in: query
          name: limit
          schema: { type: integer, default: 50, minimum: 1, maximum: 200 }
        - in: query
          name: offset
          schema: { type: integer, default: 0, minimum: 0 }
      responses:
        '200':
          description: Products for Figma with media variants
          content:
            application/json:
              schema:
                type: object
                properties:
                  count: { type: integer }
                  results:
                    type: array
                    items:
                      type: object
                      properties:
                        id: { type: string }
                        name: { type: string }
                        price:
                          type: object
                          properties:
                            value: { type: number }
                            currency: { type: string, default: EUR }
                            pretty: { type: string }
                        category:
                          type: array
                          items: { type: string }
                        season: { type: integer, nullable: true }
                        cert: { type: string, nullable: true }
                        media:
                          type: object
                          properties:
                            hero:
                              type: object
                              properties:
                                alt: { type: string, nullable: true }
                                aspectRatio: { type: number, nullable: true }
                                variants:
                                  type: object
                                  properties:
                                    thumb: { type: string, format: uri }
                                    preview: { type: string, format: uri }
                                    print: { type: string, format: uri }
                            detail:
                              type: array
                              items:
                                type: object
                                properties:
                                  alt: { type: string, nullable: true }
                                  aspectRatio: { type: number, nullable: true }
                                  variants:
                                    type: object
                                    properties:
                                      thumb: { type: string, format: uri }
                                      preview: { type: string, format: uri }
                                      print: { type: string, format: uri }
                            lifestyle:
                              type: array
                              items:
                                type: object
                                properties:
                                  alt: { type: string, nullable: true }
                                  aspectRatio: { type: number, nullable: true }
                                  variants:
                                    type: object
                                    properties:
                                      thumb: { type: string, format: uri }
                                      preview: { type: string, format: uri }
                                      print: { type: string, format: uri }
                        datasheets:
                          type: array
                          items:
                            type: object
                            properties:
                              title: { type: string }
                              url: { type: string, format: uri }
                        layout:
                          type: object
                          properties:
                            recommendedTemplate: { type: string }
                            bleed:
                              type: object
                              properties:
                                mm: { type: number }
                            dpi: { type: integer }
```

## 8) Security & Ops
- API key via `X-API-Key`; dev default allowed locally; prod must set env.
- CORS: restrict to tool and plugin origins in prod.
- Optional signed media URLs for print quality.
- Logging: record mode=preview/print requests for usage analytics.

## 9) Acceptance Criteria
- Designers can place N selected products as Figma frames within 30 seconds for 50 items on a modern laptop.
- Design mode uses low-res assets; zoom and pan remain responsive (<16ms frame budget typical).
- “Prepare for Print & Export PDF” swaps all image URLs to print variants, exports a vector+hi-res PDF, and restores preview within one operation.
- API returns consistent media roles with all three variants; 100% of items in dataset validated against schema.
- Media server responds within p95 < 300ms for preview assets at 1024px.

## 10) Test Plan
- Contract tests for `/v1/figma-feed` shape and required fields.
- Visual regression of Figma templates (golden PNGs) in preview mode.
- PDF spot checks: inspect output DPI, dimensions, and sharpness.
- Failure injection: broken URLs fall back to placeholders, export still completes.

## 11) Implementation Notes
- Server: reuse existing product loading; add a formatter to build v2 feed with `variants` from a deterministic media path schema based on product/media IDs.
- Client: small SPA with `facets` + `products` endpoints; output Manifest.
- Plugin: TypeScript; persist state in `figma.clientStorage`; include a simple UI with three buttons (Import, Place, Export).

---
v1.0 — Draft prepared to guide coding AI and team implementation.


