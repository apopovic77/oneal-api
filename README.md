# O’Neal Product API (v1)

FastAPI implementation of a read-only product API for O’Neal (MX/MTB), with API-Key auth and JSON-backed data.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_KEY=oneal_demo_token
uvicorn app.main:app --reload
```

API root: http://localhost:8000/v1

Auth header: `X-API-Key: oneal_demo_token`

## Endpoints
- GET `/v1/ping`
- GET `/v1/products` (filters: `search, category, season, cert, price_min, price_max, sort, order, limit, offset, format=figma-feed`)
- GET `/v1/products/{id}`
- GET `/v1/facets`

## Example
```bash
curl -H "X-API-Key: oneal_demo_token" "http://localhost:8000/v1/products?category=Helmets&season=2026&cert=DOT&limit=20"
```

## Data source
- Current: `app/data/products.json`
- Future: SQLite or Excel → JSON cache builder

## Dev tools
- Lint: `ruff .`
- Dev server: `uvicorn app.main:app --reload`

## Docker
```bash
docker build -t oneal-api:latest .
docker run -p 8000:8000 -e API_KEY=oneal_demo_token oneal-api:latest
```
