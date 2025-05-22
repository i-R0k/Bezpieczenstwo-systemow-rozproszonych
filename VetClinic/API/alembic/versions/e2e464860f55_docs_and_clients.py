# alembic/versions/e2e464860f55_docs_and_clients.py

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e2e464860f55'
down_revision = 'b1cf6ca335b5'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # usuń pozostałości po poprzedniej próbie
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_clients")
    # --- migracja dla clients ---
    with op.batch_alter_table('clients') as batch_op:
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
            server_default=sa.false()
        ))
    # --- migracja dla doctors ---
    with op.batch_alter_table('doctors') as batch_op:
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
            server_default=sa.false()
        ))


def downgrade() -> None:
    with op.batch_alter_table('doctors') as batch_op:
        batch_op.drop_column('must_change_password')
        batch_op.drop_column('backup_email')
    with op.batch_alter_table('clients') as batch_op:
        batch_op.drop_column('must_change_password')
        batch_op.drop_column('backup_email')
