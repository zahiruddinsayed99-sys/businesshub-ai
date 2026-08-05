import re
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator


class TenantOnboardRequest(BaseModel):
    name: Optional[str] = None
    org_name: Optional[str] = None
    slug: Optional[str] = None
    email: Optional[EmailStr] = None
    admin_email: Optional[EmailStr] = None
    password: Optional[str] = None
    admin_password: Optional[str] = None
    full_name: Optional[str] = None
    admin_full_name: Optional[str] = None

    @field_validator("slug")
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        v_str = str(v).strip()
        # Strict regex constraint: no uppercase or special characters allowed
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v_str):
            raise ValueError("Slug must contain only lowercase alphanumeric characters and hyphens")
        if len(v_str) < 2 or len(v_str) > 100:
            raise ValueError("Slug must be between 2 and 100 characters")
        return v_str

    @model_validator(mode="after")
    def validate_required_fields(self) -> "TenantOnboardRequest":
        effective_name = self.name or self.org_name
        if not effective_name or len(effective_name.strip()) < 2:
            raise ValueError("Organization name must be at least 2 characters")

        effective_email = self.email or self.admin_email
        if not effective_email:
            raise ValueError("Email is required")

        effective_password = self.password or self.admin_password
        if not effective_password or len(effective_password.strip()) < 8:
            raise ValueError("Password must be at least 8 characters long")

        effective_full_name = self.full_name or self.admin_full_name
        if not effective_full_name or len(effective_full_name.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")

        return self

    @property
    def resolved_org_name(self) -> str:
        return (self.name or self.org_name or "").strip()

    @property
    def resolved_email(self) -> str:
        return (self.email or self.admin_email or "").strip()

    @property
    def resolved_password(self) -> str:
        return (self.password or self.admin_password or "").strip()

    @property
    def resolved_full_name(self) -> str:
        return (self.full_name or self.admin_full_name or "").strip()


class StandardOnboardSuccessData(BaseModel):
    organization_id: uuid.UUID
    user_id: uuid.UUID
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class StandardOnboardResponse(BaseModel):
    status: str = "success"
    data: StandardOnboardSuccessData


class TenantOnboardResponse(BaseModel):
    organization_id: uuid.UUID
    org_name: str
    slug: str
    admin_user_id: uuid.UUID
    admin_email: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class SlugCheckResponse(BaseModel):
    slug: str
    available: bool


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    subscription_status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    subscription_status: Optional[str] = None
