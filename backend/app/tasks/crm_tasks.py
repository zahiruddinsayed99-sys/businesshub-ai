import uuid
import asyncio
from datetime import datetime, timezone
from celery import shared_task
from app.core.redis import get_redis_client
from app.core.database import get_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select, update, func
from app.domain.ai.gateway import AiGatewayService
from app.domain.models.crm_deal import CrmDeal


async def _calculate_lead_score_async(task, deal_id: uuid.UUID):
    redis = await get_redis_client()
    lock_key = f"ai_lock:score:{str(deal_id)}"

    # Acquire a Redis idempotency lock with a 2-minute TTL
    acquired = await redis.set(lock_key, "1", nx=True, ex=120)
    if not acquired:
        return {"status": "duplicate_run", "deal_id": str(deal_id)}

    try:
        engine = get_engine()
        SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
        async with SessionLocal() as db:
            gateway = AiGatewayService(db)

            try:
                # Query organization_id for the deal
                result = await db.execute(select(CrmDeal.organization_id).where(CrmDeal.id == deal_id))
                organization_id = result.scalars().first()
                if not organization_id:
                    return {"status": "error", "message": "Deal not found"}

                # In a real scenario, we'd query historical contacts/notes linked to the deal here
                context = {"deal_id": str(deal_id)}

                # Call AiGatewayService using the lead_scoring_v1 prompt template
                prompt_result = await gateway.execute_prompt(organization_id, "lead_scoring_v1", context)

                # Persist the score and JSON array back to PostgreSQL
                stmt = update(CrmDeal).where(
                    CrmDeal.id == deal_id
                ).values(
                    lead_score=prompt_result.get("score"),
                    intent_signals=prompt_result.get("intent_signals"),
                    last_scored_at=func.now()
                )

                await db.execute(stmt)
                await db.commit()

            except Exception as e:
                error_str = str(e)
                # Catch transient provider errors
                if "429" in error_str or "rate" in error_str.lower() or "timeout" in error_str.lower():
                    await redis.delete(lock_key)
                    raise task.retry(exc=e, countdown=2 ** task.request.retries)
                raise e

        return {"status": "completed", "deal_id": str(deal_id)}
    finally:
        # Note: We keep the lock until it expires to prevent duplicate runs shortly after completion.
        # But if you want to release it immediately, you'd do: await redis.delete(lock_key)
        pass
