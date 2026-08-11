from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/healthz", status_code=200, tags=["Health"])
async def health_check():
    """Basic health check endpoint returning status 200 OK."""
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
