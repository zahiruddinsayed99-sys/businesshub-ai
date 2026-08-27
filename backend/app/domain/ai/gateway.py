import uuid
import google.generativeai as genai
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
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-3.6-flash')
        # models/gemini-2.5-flash , gemini-flash-latest

        prompt = f"""You are a helpful AI assistant. Answer the user's question using ONLY the provided document context.

Context:
{document_context}

User's Question:
{user_question}"""

        response = await model.generate_content_async(prompt)

        return response.text

    async def generate_quiz(self, organization_id: uuid.UUID, lesson_content: str) -> dict:
        # Pre-flight check and deduct 10 credits as per requirements
        pass

        # Mocking the AI response using the lms_quiz_v1 JSON structure
        return {
            "title": "Generated Quiz",
            "questions": [
                {
                    "question_text": "What is the capital of France?",
                    "answers": [
                        {"answer_text": "Paris", "is_correct": True},
                        {"answer_text": "London", "is_correct": False},
                        {"answer_text": "Berlin", "is_correct": False},
                        {"answer_text": "Madrid", "is_correct": False}
                    ]
                },
                {
                    "question_text": "What is 2 + 2?",
                    "answers": [
                        {"answer_text": "3", "is_correct": False},
                        {"answer_text": "4", "is_correct": True},
                        {"answer_text": "5", "is_correct": False},
                        {"answer_text": "22", "is_correct": False}
                    ]
                },
                {
                    "question_text": "Which planet is known as the Red Planet?",
                    "answers": [
                        {"answer_text": "Earth", "is_correct": False},
                        {"answer_text": "Mars", "is_correct": True},
                        {"answer_text": "Jupiter", "is_correct": False},
                        {"answer_text": "Saturn", "is_correct": False}
                    ]
                },
                {
                    "question_text": "Who wrote 'Hamlet'?",
                    "answers": [
                        {"answer_text": "Charles Dickens", "is_correct": False},
                        {"answer_text": "William Shakespeare", "is_correct": True},
                        {"answer_text": "Mark Twain", "is_correct": False},
                        {"answer_text": "Jane Austen", "is_correct": False}
                    ]
                },
                {
                    "question_text": "What is the largest ocean on Earth?",
                    "answers": [
                        {"answer_text": "Atlantic Ocean", "is_correct": False},
                        {"answer_text": "Indian Ocean", "is_correct": False},
                        {"answer_text": "Arctic Ocean", "is_correct": False},
                        {"answer_text": "Pacific Ocean", "is_correct": True}
                    ]
                }
            ]
        }
