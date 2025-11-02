"""add_post_id_to_publication_queue

Revision ID: 2ca98b92d3e5
Revises: 2f0fe8c89379
Create Date: 2025-11-02 22:46:01.347699

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2ca98b92d3e5'
down_revision = '2f0fe8c89379'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ajouter post_id à publication_queue (sans clé étrangère pour l'instant car table posts n'existe pas encore)
    # La clé étrangère pourra être ajoutée plus tard via une autre migration quand la table posts sera créée
    
    # Ajouter simplement la colonne post_id
    op.add_column('publication_queue', sa.Column('post_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Supprimer post_id de publication_queue
    from alembic import context
    from sqlalchemy import inspect
    
    connection = context.get_bind()
    inspector = inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('publication_queue')]
    
    if 'post_id' in columns:
        try:
            op.drop_constraint('publication_queue_post_id_fkey', 'publication_queue', type_='foreignkey')
        except Exception:
            pass
        op.drop_column('publication_queue', 'post_id')



