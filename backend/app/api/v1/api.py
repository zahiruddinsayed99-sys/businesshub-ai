from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    health,
    organizations,
    tenants,
    crm_deals,
    billing,
    ai,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(crm_deals.router, prefix="/crm/deals", tags=["CRM Deals"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
from app.api.v1.lms import authoring
from app.api.v1.lms import learner
api_router.include_router(authoring.router, prefix="/lms", tags=["LMS Authoring"])
api_router.include_router(learner.router, prefix="/lms", tags=["LMS Learner"])
