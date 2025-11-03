"""add_audit_logs_table

Revision ID: 20251103221837
Revises: 2ca98b92d3e5
Create Date: 2025-11-03 22:18:37.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251103221837'
down_revision = '2ca98b92d3e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Créer la table audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('action_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Créer les index pour performance
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('idx_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    # Supprimer les index
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    
    # Supprimer la table
    op.drop_table('audit_logs')

