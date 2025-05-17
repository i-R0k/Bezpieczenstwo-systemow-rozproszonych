"""Remove

Revision ID: 32d8e9ecdd2d
Revises: 0bf2f39b9b0c
Create Date: 2025-05-17 12:27:41.315265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '32d8e9ecdd2d'
down_revision: Union[str, None] = '0bf2f39b9b0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Ustaw NOT NULL na kolumnie facility_id w appointments (działa w SQLite tylko przez batch)
    with op.batch_alter_table('appointments', recreate='always') as batch_op:
        batch_op.alter_column('facility_id', nullable=False)

def downgrade() -> None:
    """Downgrade schema."""
    # Zmień z powrotem na NULLable, jeśli robisz downgrade
    with op.batch_alter_table('appointments', recreate='always') as batch_op:
        batch_op.alter_column('facility_id', nullable=True)
