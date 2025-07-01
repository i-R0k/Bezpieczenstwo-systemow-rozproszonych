"""add tx_hash to appointments

Revision ID: a69c226e2577
Revises: 475b1af14e99
Create Date: 2025-06-29 14:50:09.126870

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a69c226e2577'
down_revision = '475b1af14e99'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema: dodajemy tx_hash do appointments."""
    op.add_column(
        'appointments',
        sa.Column(
            'tx_hash',
            sa.String(length=66),
            nullable=True,
            comment='Hash transakcji on‐chain'
        )
    )

def downgrade() -> None:
    """Downgrade schema: usuwamy tx_hash z appointments."""
    op.drop_column('appointments', 'tx_hash')
