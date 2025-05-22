"""Consultant

Revision ID: 11cd31fb8dec
Revises: 32d8e9ecdd2d
Create Date: 2025-05-17 17:04:03.490333

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11cd31fb8dec'
down_revision: Union[str, None] = '32d8e9ecdd2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # batch_alter_table automatycznie wykryje SQLite i użyje copy-and-move
    with op.batch_alter_table('consultants', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('facility_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_consultants_facility',
            'facilities',
            ['facility_id'], ['id']
        )

def downgrade():
    with op.batch_alter_table('consultants', schema=None) as batch_op:
        batch_op.drop_constraint('fk_consultants_facility', type_='foreignkey')
        batch_op.drop_column('facility_id')
