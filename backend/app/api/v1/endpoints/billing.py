from starlette.concurrency import run_in_threadpool
import uuid
import stripe
from typing import Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import redis.asyncio as aioredis
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.tenant_middleware import TenantContext, get_tenant_context
from app.core.rbac import RequiresPermission
from app.core.config import settings
from app.domain.models.organization import Organization

router = APIRouter()

stripe.api_key = settings.STRIPE_API_KEY

@router.post("/checkout")
async def create_checkout_session(
    request: Request,
    context: TenantContext = Depends(RequiresPermission("tenant:billing")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).where(Organization.id == context.organization_id)
    result = await db.execute(stmt)
    organization = result.scalars().first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        if not settings.STRIPE_API_KEY or "dummy" in settings.STRIPE_API_KEY.lower():
            return {"url": "https://billing.stripe.com/test-portal"}

        customer_id = organization.stripe_customer_id
        if not customer_id:
            customer = await run_in_threadpool(stripe.Customer.create,
                name=organization.name,
                metadata={"organization_id": str(organization.id)}
            )
            customer_id = customer.id
            organization.stripe_customer_id = customer_id
            await db.commit()

        session_kwargs = {
            "customer": customer_id,
            "payment_method_options": {"card": {"request_three_d_secure": "any"}},
            "allow_promotion_codes": True,
            "automatic_tax": {"enabled": True},
            "mode": "subscription",
            "line_items": [{
                "price_data": {
                    "currency": "inr",
                    "product_data": {
                        "name": "Pro Subscription"
                    },
                    "unit_amount": 100000,
                    "recurring": {"interval": "month"}
                },
                "quantity": 1,
            }],
            "success_url": "http://localhost:4200/billing/success",
            "cancel_url": "http://localhost:4200/billing/cancel",
        }

        if organization.gstin:
            await run_in_threadpool(stripe.Customer.create_tax_id,
                customer_id,
                type="in_gst",
                value=organization.gstin
            )

        checkout_session = await run_in_threadpool(stripe.checkout.Session.create,**session_kwargs)

        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/portal")
async def create_customer_portal(
    request: Request,
    context: TenantContext = Depends(RequiresPermission("tenant:billing")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).where(Organization.id == context.organization_id)
    result = await db.execute(stmt)
    organization = result.scalars().first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        if not settings.STRIPE_API_KEY or "dummy" in settings.STRIPE_API_KEY.lower():
            return {"url": "https://billing.stripe.com/test-portal"}

        customer_id = organization.stripe_customer_id
        if not customer_id:
            customer = await run_in_threadpool(stripe.Customer.create,
                name=organization.name,
                metadata={"organization_id": str(organization.id)}
            )
            customer_id = customer.id
            organization.stripe_customer_id = customer_id
            await db.commit()

        portal_session = await run_in_threadpool(stripe.billing_portal.Session.create,
            customer=organization.stripe_customer_id,
            return_url="http://localhost:4200/billing"
        )
        return {"url": portal_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhooks")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    payload = await request.body()
    try:
        event = await run_in_threadpool(stripe.Webhook.construct_event,
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_id = event.get("id")
    event_type = event.get("type")
    event_created = event.get("created")

    lock_key = f"stripe_lock:{event_id}"
    final_key = f"stripe_evt:{event_id}"

    if await redis.exists(final_key):
        return {"status": "success", "message": "Already processed"}

    acquired = await redis.set(lock_key, "1", nx=True, ex=10)
    if not acquired:
        raise HTTPException(status_code=409, detail="Concurrent processing")

    try:
        if event_type in ["customer.subscription.updated", "customer.subscription.deleted"]:
            subscription = event.data.object
            customer_id = subscription.customer
            status = subscription.status

            stmt = select(Organization).where(Organization.stripe_customer_id == customer_id)
            result = await db.execute(stmt)
            organization = result.scalars().first()

            if organization:
                event_ts = datetime.fromtimestamp(event_created, tz=timezone.utc)
                if organization.last_billing_event_ts and event_ts <= organization.last_billing_event_ts:
                    await redis.delete(lock_key)
                    return {"status": "success", "message": "Out of order event discarded"}

                organization.subscription_status = status.upper()
                organization.stripe_subscription_id = subscription.id
                organization.last_billing_event_ts = event_ts

                if status == "active":
                    organization.subscription_tier = "PRO"
                elif event_type == "customer.subscription.deleted" or status in ["canceled", "unpaid", "past_due"]:
                    organization.subscription_tier = "FREE"

                await db.commit()

        await redis.set(final_key, "1", ex=86400)
    except Exception as e:
        await redis.delete(lock_key)
        raise e
    finally:
        await redis.delete(lock_key)

    return {"status": "success"}
