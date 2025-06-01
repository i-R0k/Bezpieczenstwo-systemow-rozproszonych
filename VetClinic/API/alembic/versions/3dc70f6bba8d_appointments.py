"""Appointments

Revision ID: 3dc70f6bba8d
Revises: 5a4fe9dee3cd
Create Date: 2025-06-01 14:38:56.845916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3dc70f6bba8d'
down_revision: Union[str, None] = '5a4fe9dee3cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 0) Usuń pozostałą tabelę tymczasową, jeśli istnieje (SQLite batch alter cleanup)
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_appointments;")

    # 1) Usuń duplikaty w tabeli 'appointments', pozostawiając tylko MIN(rowid) dla każdej pary (doctor_id, visit_datetime)
    op.execute(
        """
        DELETE FROM appointments
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM appointments
            GROUP BY doctor_id, visit_datetime
        )
        """
    )

    # 2) W batch mode utwórz unikalne ograniczenie (doctor_id, visit_datetime)
    with op.batch_alter_table('appointments', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_doctor_visit_datetime',
            ['doctor_id', 'visit_datetime']
        )

    # 3) Usuń kolumnę 'backup_email' z tabeli 'clients'
    op.drop_column('clients', 'backup_email')


def downgrade() -> None:
    """Downgrade schema."""
    # 1) W batch mode usuń unikalne ograniczenie (doctor_id, visit_datetime)
    with op.batch_alter_table('appointments', schema=None) as batch_op:
        batch_op.drop_constraint('uq_doctor_visit_datetime', type_='unique')

    # 2) Przywróć kolumnę 'backup_email' w tabeli 'clients'
    op.add_column(
        'clients',
        sa.Column('backup_email', sa.VARCHAR(), server_default=sa.text("('')"), nullable=False)
    )
