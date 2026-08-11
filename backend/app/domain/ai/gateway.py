import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.core.billing import consume_ai_credits_br_plt_002, check_soft_lock_overage

class AiGatewayService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def pre_flight_check(self, organization_id: uuid.UUID, credit_cost: int = 1) -> None:
        if not organization_id:
            raise HTTPException(status_code=403, detail="ERR_RBAC_001")

        await check_soft_lock_overage(self.session, organization_id)
        await consume_ai_credits_br_plt_002(self.session, organization_id, credit_cost)

    async def generate_embeddings(self, organization_id: uuid.UUID, text_content: str) -> list[float]:
        # Pre-flight check and deduct credits
        await self.pre_flight_check(organization_id, credit_cost=1)

        # Mock embedding generation for now
        # In a real scenario, this would call an external API like OpenAI
        return [0.1] * 1536

    async def execute_prompt(self, organization_id: uuid.UUID, template_name: str, context: Dict[str, Any]) -> Any:
        # Pre-flight check and deduct credits
        await self.pre_flight_check(organization_id, credit_cost=1)

        # Mocking prompt execution response
        if template_name == "lead_scoring_v1":
            return {"score": 85, "intent_signals": ["high_email_engagement", "pricing_page_visit"]}
        elif template_name == "crm_followup_v1":
            return "Here is a follow-up email draft based on the context."
        return {}
