import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class TenantOnboardRequest(BaseModel):
    org_name: str
    slug: Optional[str] = None
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str

    @field_validator("org_name")
    def validate_org_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 255:
            raise ValueError("Organization name must be between 2 and 255 characters")
        return v

    @field_validator("slug")
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError("Slug must contain only lowercase alphanumeric characters and hyphens")
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Slug must be between 2 and 100 characters")
        return v

    @field_validator("admin_password")
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("admin_full_name")
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 255:
            raise ValueError("Admin full name must be between 2 and 255 characters")
        return v


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
