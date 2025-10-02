"""init tables

Revision ID: 20251001_0001
Revises: 
Create Date: 2025-10-01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251001_0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'approvals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amount_usd', sa.Float(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('threshold', sa.Float(), nullable=False, server_default='50'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        'artifacts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kind', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('meta', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_table(
        'runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('run_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='created'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

def downgrade():
    op.drop_table('runs')
    op.drop_table('artifacts')
    op.drop_table('approvals')
