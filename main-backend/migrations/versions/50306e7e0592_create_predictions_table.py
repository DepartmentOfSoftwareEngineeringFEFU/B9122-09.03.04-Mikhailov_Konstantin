from typing import Sequence, Union

from alembic import op

import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

revision: str = '50306e7e0592'

down_revision: Union[str, Sequence[str], None] = None

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:

    op.create_table('predictions',

    sa.Column('id', sa.UUID(), nullable=False),

    sa.Column('user_id', sa.UUID(), nullable=False),

    sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),

    sa.Column('predicted_price', sa.Float(), nullable=False),

    sa.Column('predicted_price_per_sqm', sa.Float(), nullable=False),

    sa.Column('horizon', sa.String(length=20), nullable=False),

    sa.Column('confidence', sa.Float(), nullable=False),

    sa.Column('model_version', sa.String(length=50), nullable=False),

    sa.Column('status', sa.String(length=20), nullable=False),

    sa.Column('comparables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

    sa.Column('error_message', sa.Text(), nullable=True),

    sa.Column('ip_address', postgresql.INET(), nullable=True),

    sa.Column('user_agent', sa.Text(), nullable=True),

    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

    sa.PrimaryKeyConstraint('id')

    )

    op.create_index('idx_predictions_created_at', 'predictions', ['created_at'], unique=False)

    op.create_index('idx_predictions_status', 'predictions', ['status'], unique=False)

    op.create_index('idx_predictions_user_id', 'predictions', ['user_id'], unique=False)

    op.create_index(op.f('ix_predictions_user_id'), 'predictions', ['user_id'], unique=False)

def downgrade() -> None:

    op.drop_index(op.f('ix_predictions_user_id'), table_name='predictions')

    op.drop_index('idx_predictions_user_id', table_name='predictions')

    op.drop_index('idx_predictions_status', table_name='predictions')

    op.drop_index('idx_predictions_created_at', table_name='predictions')

    op.drop_table('predictions')
