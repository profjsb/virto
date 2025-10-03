"""roles + run_logs

Revision ID: 20251001_0003
Revises: 20251001_0002
Create Date: 2025-10-01
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '20251001_0003'
down_revision = '20251001_0002'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=64), nullable=False, unique=True),
    )
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
    )
    op.create_table(
        'run_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('level', sa.String(length=16), nullable=False, server_default='info'),
        sa.Column('message', sa.Text(), nullable=False),
    )

def downgrade():
    op.drop_table('run_logs')
    op.drop_table('user_roles')
    op.drop_table('roles')
