"""Update currency default to INR

Revision ID: 83a80f502b8e
Revises: 423b64ae23ff
Create Date: 2026-08-27 08:13:00.360182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83a80f502b8e'
down_revision: Union[str, None] = '423b64ae23ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('crm_deals', 'currency', server_default="INR")


def downgrade() -> None:
    op.alter_column('crm_deals', 'currency', server_default="USD")
