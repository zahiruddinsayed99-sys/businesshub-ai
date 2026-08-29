"""merge ai jobs and crm tasks

Revision ID: 423b64ae23ff
Revises: 314159265358, acf834a0754d
Create Date: 2026-08-26 05:00:15.071643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '423b64ae23ff'
down_revision: Union[str, None] = ('314159265358', 'acf834a0754d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
