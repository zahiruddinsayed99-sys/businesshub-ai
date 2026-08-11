import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, text, DateTime, Integer
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user_role import UserRole

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    subscription_tier: Mapped[str] = mapped_column(
        String(20), server_default="FREE", default="FREE", nullable=False
    )
    subscription_status: Mapped[str] = mapped_column(
        String(20), server_default="INACTIVE", default="INACTIVE", nullable=False
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    gstin: Mapped[str] = mapped_column(String(15), nullable=True)
    billing_state: Mapped[str] = mapped_column(String(50), nullable=True)
    ai_credits_used: Mapped[int] = mapped_column(Integer, server_default="0", default=0, nullable=False)
    bonus_ai_credits: Mapped[int] = mapped_column(Integer, server_default="0", default=0, nullable=False)
    last_billing_event_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="organization", cascade="all, delete-orphan"
    )
