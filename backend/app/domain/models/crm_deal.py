import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Numeric, DateTime, ForeignKey, text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.organization import Organization
    from app.domain.models.contact import Contact
    from app.domain.models.user import User


class CrmDeal(Base, TimestampMixin):
    __tablename__ = "crm_deals"

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
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    value_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), server_default="USD", default="USD", nullable=False)
    stage: Mapped[str] = mapped_column(String(50), server_default="LEAD", default="LEAD", nullable=False)
    expected_close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    contact: Mapped[Optional["Contact"]] = relationship("Contact")
    owner: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index(
            "ix_crm_deals_org_stage_active",
            "organization_id", "stage",
            postgresql_where=text("deleted_at IS NULL")
        ),
    )
