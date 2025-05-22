"""add_backup_email_and_must_change_password_to_consultant

Revision ID: a98c1d85e253
Revises: 96cf1625b86c
Create Date: 2025-05-17 18:02:42.593631
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a98c1d85e253'
down_revision = '96cf1625b86c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # jeśli została stara tmp‐tabela, usuń ją
    op.execute('DROP TABLE IF EXISTS "_alembic_tmp_consultants"')

    # dodajemy kolumny w batch‐mode z domyślnymi wartościami,
    # by migracja przeszła na SQLite
    with op.batch_alter_table('consultants', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'backup_email',
            sa.String(),
            nullable=False,
            server_default=''
        ))
        batch_op.add_column(sa.Column(
            'must_change_password',
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.expression.true()
        ))

def downgrade() -> None:
    # usuwamy kolumny w batch‐mode
    with op.batch_alter_table('consultants', schema=None) as batch_op:
        batch_op.drop_column('must_change_password')
        batch_op.drop_column('backup_email')
