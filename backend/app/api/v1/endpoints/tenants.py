from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.schemas.tenant import SlugCheckResponse, TenantOnboardRequest, TenantOnboardResponse
from app.services.tenant_service import TenantService

router = APIRouter()
tenant_service = TenantService()


@router.post("/onboard", response_model=TenantOnboardResponse, status_code=status.HTTP_201_CREATED)
async def onboard_tenant(
    payload: TenantOnboardRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client),
):
    """
    Onboard a new organization and admin user.
    Creates Organization, User, UserRole (ADMIN), issues RS256 token and Redis session.
    """
    return await tenant_service.onboard_tenant(
        db=db,
        redis=redis,
        response=response,
        payload=payload,
    )


@router.get("/check-slug/{slug}", response_model=SlugCheckResponse)
async def check_slug_availability(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Real-time endpoint to check if an organization slug is available."""
    return await tenant_service.check_slug_availability(db=db, slug=slug)
