"""facility

Revision ID: 0d3d0cad1cb9
Revises: 99f0c5235ccd
Create Date: 2025-06-22 17:02:05.260743
"""
from typing import Sequence, Union
from sqlalchemy import inspect, text
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0d3d0cad1cb9'
down_revision: Union[str, None] = '99f0c5235ccd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    # 0) Clean up any leftover temp table from a previous failed batch run
    op.execute(text("DROP TABLE IF EXISTS _alembic_tmp_doctors"))

    # 1) Drop invoices if it exists
    if 'invoices' in inspector.get_table_names():
        op.drop_table('invoices')

    # 2) Add facility_id column if not already present
    existing_cols = [col['name'] for col in inspector.get_columns('doctors')]
    if 'facility_id' not in existing_cols:
        op.add_column(
            'doctors',
            sa.Column('facility_id', sa.Integer(), nullable=True)
        )
        # back-fill existing rows (ensure a facility with id=1 exists)
        op.execute(text("UPDATE doctors SET facility_id = 1"))

    # 3) In batch mode, make facility_id NOT NULL and add the FK
    with op.batch_alter_table('doctors') as batch_op:
        # a) enforce NOT NULL if we just added
        if 'facility_id' not in existing_cols:
            batch_op.alter_column(
                'facility_id',
                existing_type=sa.Integer(),
                nullable=False
            )
        # b) add foreign-key if missing
        existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('doctors')]
        if 'fk_doctors_facility' not in existing_fks:
            batch_op.create_foreign_key(
                'fk_doctors_facility',
                'facilities',
                ['facility_id'], ['id']
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    # 1) Remove FK and facility_id column if they exist
    with op.batch_alter_table('doctors') as batch_op:
        existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('doctors')]
        if 'fk_doctors_facility' in existing_fks:
            batch_op.drop_constraint('fk_doctors_facility', type_='foreignkey')

        existing_cols = [col['name'] for col in inspector.get_columns('doctors')]
        if 'facility_id' in existing_cols:
            batch_op.drop_column('facility_id')

    # 2) Recreate invoices table as before
    op.create_table(
        'invoices',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('client_id', sa.INTEGER(), nullable=False),
        sa.Column('amount', sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.VARCHAR(length=20), nullable=False),
        sa.Column('created_at', sa.DATETIME(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_invoices_id', 'invoices', ['id'], unique=False)
    op.create_index('ix_invoices_client_id', 'invoices', ['client_id'], unique=False)
