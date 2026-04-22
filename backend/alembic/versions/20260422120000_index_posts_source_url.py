"""index posts.source_url for filters (B-tree)

Accélère les égalités / préfixes ; pour ILIKE '%mot%' sous PostgreSQL, un index GIN
avec pg_trgm peut être ajouté manuellement par un admin (CREATE EXTENSION pg_trgm).

Revision ID: 20260422120000
Revises: 20251103221837
Create Date: 2026-04-22 12:00:00.000000

"""
from alembic import op

revision = "20260422120000"
down_revision = "20251103221837"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_posts_source_url",
        "posts",
        ["source_url"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_posts_source_url", table_name="posts")
