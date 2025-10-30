from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import products, facets, ping, categories


app = FastAPI(title="O’Neal Product API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ping.router, prefix="/v1", tags=["health"]) 
app.include_router(products.router, prefix="/v1", tags=["products"]) 
app.include_router(facets.router, prefix="/v1", tags=["facets"]) 
app.include_router(categories.router, prefix="/v1", tags=["categories"]) 


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
