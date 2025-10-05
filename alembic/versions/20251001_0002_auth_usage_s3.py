"""auth + usage + s3 fields

Revision ID: 20251001_0002
Revises: 20251001_0001
Create Date: 2025-10-01
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '20251001_0002'
down_revision = '20251001_0001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_table(
        'usage_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('run_id', sa.Integer(), nullable=True),
        sa.Column('actor', sa.String(length=128), nullable=True),
        sa.Column('model', sa.String(length=128), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    # Extend artifacts
    op.add_column('artifacts', sa.Column('storage', sa.String(length=16), nullable=False, server_default='local'))
    op.add_column('artifacts', sa.Column('s3_bucket', sa.String(length=255), nullable=True))
    op.add_column('artifacts', sa.Column('s3_key', sa.String(length=512), nullable=True))
    op.add_column('artifacts', sa.Column('content_type', sa.String(length=128), nullable=True))

def downgrade():
    op.drop_table('usage_events')
    op.drop_table('users')
    op.drop_column('artifacts', 'content_type')
    op.drop_column('artifacts', 's3_key')
    op.drop_column('artifacts', 's3_bucket')
    op.drop_column('artifacts', 'storage')
