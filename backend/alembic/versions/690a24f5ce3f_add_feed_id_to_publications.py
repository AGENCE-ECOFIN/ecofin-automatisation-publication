"""add_feed_id_to_publications

Revision ID: 690a24f5ce3f
Revises: a544d0d64aaf
Create Date: 2025-10-13 23:28:06.496545

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '690a24f5ce3f'
down_revision = 'a544d0d64aaf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ajouter feed_id à la table publications
    op.add_column('publications', sa.Column('feed_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'publications', 'feeds', ['feed_id'], ['id'])
    
    # Nettoyer les anciennes tables/index si nécessaire
    try:
        op.drop_index('idx_global_publication_configs_network', table_name='global_publication_configs', if_exists=True)
        op.drop_table('global_publication_configs', if_exists=True)
    except:
        pass
    
    try:
        op.create_index(op.f('ix_network_configs_id'), 'network_configs', ['id'], unique=False, if_not_exists=True)
        op.create_index(op.f('ix_publication_queue_id'), 'publication_queue', ['id'], unique=False, if_not_exists=True)
    except:
        pass


def downgrade() -> None:
    # Retirer feed_id de publications
    op.drop_constraint(None, 'publications', type_='foreignkey')
    op.drop_column('publications', 'feed_id')



