"""Reset migration state - replace missing 86f346ee8d40

Revision ID: 86f346ee8d40
Revises: e59e5b4094a3
Create Date: 2025-10-27 09:34:13.633891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86f346ee8d40'
down_revision = 'e59e5b4094a3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass



