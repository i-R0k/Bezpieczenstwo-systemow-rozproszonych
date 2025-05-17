"""Add facility

Revision ID: 0bf2f39b9b0c
Revises: 8f020866ea61
Create Date: 2025-05-16 19:45:16.919642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0bf2f39b9b0c'
down_revision: Union[str, None] = '8f020866ea61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Wstawiamy domyślną placówkę
    op.execute("""
    INSERT INTO facilities (name, address, phone, created_at, updated_at)
    VALUES (
        'Default Facility',
        'Unknown Address',
        NULL,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    """)

    # 2. Wykorzystujemy batch mode, żeby SQLite poprawnie dodał kolumnę + FK
    with op.batch_alter_table('appointments') as batch_op:
        batch_op.add_column(
            sa.Column('facility_id', sa.Integer(), nullable=True),
        )
        batch_op.create_foreign_key(
            'fk_appointments_facility_id_facilities',
            'facilities',
            ['facility_id'], ['id']
        )

    # 3. Wypełniamy istniejące rekordy ID domyślnej placówki
    op.execute("""
    UPDATE appointments
    SET facility_id = (
        SELECT id FROM facilities
        WHERE name = 'Default Facility'
        LIMIT 1
    )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Usuwamy kolumnę + FK w batch mode
    with op.batch_alter_table('appointments') as batch_op:
        batch_op.drop_constraint('fk_appointments_facility_id_facilities', type_='foreignkey')
        batch_op.drop_column('facility_id')

    # 2. Usuwamy domyślną placówkę
    op.execute("""
    DELETE FROM facilities
    WHERE name = 'Default Facility'
    """)
