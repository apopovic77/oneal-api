from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from ..core.auth import api_key_auth

router = APIRouter()


@router.get("/ping")
async def ping(_: None = Depends(api_key_auth)):
    return {
        "status": "ok",
        "version": "1.0",
        "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
