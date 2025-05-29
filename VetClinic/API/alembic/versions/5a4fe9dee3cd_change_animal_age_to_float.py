"""Change animal.age to Float

Revision ID: 5a4fe9dee3cd
Revises: 061c4512b7bc
Create Date: 2025-05-25 18:35:14.969419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a4fe9dee3cd'
down_revision: Union[str, None] = '061c4512b7bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table("animals") as batch_op:
        batch_op.alter_column(
            "age",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=True,
        )

def downgrade():
    with op.batch_alter_table("animals") as batch_op:
        batch_op.alter_column(
            "age",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
