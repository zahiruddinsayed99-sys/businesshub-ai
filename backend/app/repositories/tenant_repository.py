import re
import uuid
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.organization import Organization
from app.domain.models.user import User
from app.domain.models.user_role import UserRole


class TenantRepository:

    @staticmethod
    def generate_slug(name: str) -> str:
        """Convert an organization name into a URL-friendly slug."""
        slug = name.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_-]+", "-", slug)
        slug = re.sub(r"^-+|-+$", "", slug)
        return slug or "org"

    async def get_org_by_slug(self, db: AsyncSession, slug: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.slug == slug)
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_org_by_id(self, db: AsyncSession, org_id: uuid.UUID) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.id == org_id)
        res = await db.execute(stmt)
        return res.scalars().first()

    async def create_tenant(
        self,
        db: AsyncSession,
        org_name: str,
        slug: str,
        admin_email: str,
        hashed_password: str,
        admin_full_name: str,
        role: str = "TENANT_OWNER",
        secondary_email: Optional[str] = None,
        secondary_hashed_password: Optional[str] = None,
        secondary_full_name: Optional[str] = None,
        secondary_role: str = "DOMAIN_MEMBER"
    ) -> Tuple[Organization, User, UserRole]:
        """Atomically create Organization, Admin User, and UserRole inside single transaction."""
        org = Organization(
            name=org_name,
            slug=slug,
            subscription_status="FREE",
        )
        db.add(org)
        await db.flush()  # Populates org.id

        user = User(
            email=admin_email,
            hashed_password=hashed_password,
            full_name=admin_full_name,
            is_active=True,
        )
        db.add(user)
        await db.flush()  # Populates user.id

        user_role = UserRole(
            user_id=user.id,
            organization_id=org.id,
            role=role,
        )
        db.add(user_role)

        # If secondary user details provided (Admin Tool Onboarding), create them too
        if secondary_email and secondary_hashed_password and secondary_full_name:
            sec_user = User(
                email=secondary_email,
                hashed_password=secondary_hashed_password,
                full_name=secondary_full_name,
                is_active=True,
            )
            db.add(sec_user)
            await db.flush()

            sec_role = UserRole(
                user_id=sec_user.id,
                organization_id=org.id,
                role=secondary_role,
            )
            db.add(sec_role)

        await db.commit()

        await db.refresh(org)
        await db.refresh(user)

        return org, user, user_role

    async def update_organization(
        self,
        db: AsyncSession,
        org: Organization,
        name: Optional[str] = None,
        subscription_status: Optional[str] = None,
        gstin: Optional[str] = None,
        billing_state: Optional[str] = None,
    ) -> Organization:
        if name is not None:
            org.name = name
        if subscription_status is not None:
            org.subscription_status = subscription_status
        if gstin is not None:
            org.gstin = gstin
        if billing_state is not None:
            org.billing_state = billing_state
        db.add(org)
        await db.commit()
        await db.refresh(org)
        return org
