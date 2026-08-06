from app.core.celery_app import celery_app
import asyncio

@celery_app.task(bind=True, name="crm.calculate_lead_score")
def calculate_lead_score(self, deal_id_str: str):
    return {"status": "completed", "deal_id": deal_id_str, "score": 85}
