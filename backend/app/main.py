from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hata", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

from app.api.regions import router as regions_router
from app.api.listings import router as listings_router
from app.api.parser import router as parser_router
from app.api.stats import router as stats_router

app.include_router(regions_router)
app.include_router(listings_router)
app.include_router(parser_router)
app.include_router(stats_router)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
