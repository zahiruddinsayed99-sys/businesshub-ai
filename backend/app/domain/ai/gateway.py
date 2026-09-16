import uuid
import json
from google import genai
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.core.billing import consume_ai_credits_br_plt_002, check_soft_lock_overage
from app.core.config import settings

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
        # In a real scenario, this would call an external API like Gemini via google-generativeai
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

    async def execute_rag_chat(self, organization_id: uuid.UUID, document_context: str, user_question: str) -> str:
        # Pre-flight check and deduct credits
        await self.pre_flight_check(organization_id, credit_cost=2)

        if not settings.GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""You are a helpful AI assistant. Answer the user's question using ONLY the provided document context.

Context:
{document_context}

User's Question:
{user_question}"""

        response = await client.aio.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt
        )

        return response.text

    async def generate_quiz(self, organization_id: uuid.UUID, lesson_content: str) -> dict:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        print("GEMINI_API_KEY= "+settings.GEMINI_API_KEY)  # Debugging line to check the API key

        prompt = f"""You are an expert instructional designer. Generate a quiz based strictly on the provided lesson content.
The output MUST be valid JSON and contain a title and a list of questions. Each question MUST have exactly 4 answers, with only one correct answer.

Lesson Content:
{lesson_content}

Output Format:
{{
  "title": "Quiz Title",
  "questions": [
    {{
      "question_text": "Question 1 text?",
      "answers": [
        {{"answer_text": "Answer 1", "is_correct": true}},
        {{"answer_text": "Answer 2", "is_correct": false}},
        {{"answer_text": "Answer 3", "is_correct": false}},
        {{"answer_text": "Answer 4", "is_correct": false}}
      ]
    }}
  ]
}}
"""
        response = await client.aio.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt
        )
        text = response.text.strip()

        # Strip markdown formatting if any
        if text.startswith("```json"):
            text = text[7:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

        return json.loads(text)
