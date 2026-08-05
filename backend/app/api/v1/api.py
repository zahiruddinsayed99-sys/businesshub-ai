from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, organizations, tenants

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
