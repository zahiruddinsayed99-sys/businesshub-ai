from pydantic import BaseModel, EmailStr, Field, ConfigDict
import re

class OnboardTenantRequest(BaseModel):
    # Organization Fields
    name: str = Field(..., min_length=3, max_length=100, description="Name of the organization")
    slug: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-z0-9-]{3,30}$", description="Organization slug")

    # User Fields
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., description="User full name")

    model_config = ConfigDict(from_attributes=True)

class InvitationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to invite")

class InvitationResponse(BaseModel):
    token: str = Field(..., description="Plaintext invitation token")

class InviteAcceptRequest(BaseModel):
    token: str = Field(..., description="Plaintext invitation token")
    full_name: str = Field(..., min_length=2, description="User full name")
    password: str = Field(..., min_length=8, description="User password")
