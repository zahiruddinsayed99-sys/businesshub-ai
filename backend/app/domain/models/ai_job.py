import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.domain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.organization import Organization

class AiJob(Base, TimestampMixin):
    __tablename__ = "ai_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), server_default="PENDING", default="PENDING", nullable=False)
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
