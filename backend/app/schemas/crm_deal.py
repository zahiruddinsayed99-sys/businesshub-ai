import uuid
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CrmDealBase(BaseModel):
    title: str
    value_amount: float
    currency: str = "INR"
    stage: str = "LEAD"
    contact_id: Optional[uuid.UUID] = None
    owner_user_id: Optional[uuid.UUID] = None
    expected_close_date: Optional[datetime] = None

class CrmDealCreate(CrmDealBase):
    pass

class CrmDealUpdateStage(BaseModel):
    stage: str

class CrmDealUpdate(BaseModel):
    title: Optional[str] = None
    value_amount: Optional[float] = None
    currency: Optional[str] = None
    stage: Optional[str] = None
    contact_id: Optional[uuid.UUID] = None
    owner_user_id: Optional[uuid.UUID] = None
    expected_close_date: Optional[datetime] = None

class CrmDealResponse(CrmDealBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
