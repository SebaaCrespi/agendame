"""turnos: auditoria de reasignacion (CU-08)

Revision ID: c8d1e2f3a4b5
Revises: a35d0eb30f66
Create Date: 2026-11-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d1e2f3a4b5'
down_revision: Union[str, None] = 'a35d0eb30f66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('turnos', sa.Column('reasignado_desde', sa.DateTime(timezone=True), nullable=True))
    op.add_column('turnos', sa.Column('motivo_reasignacion', sa.Text(), nullable=True))
    op.add_column('turnos', sa.Column('reasignado_en', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('turnos') as batch_op:
        batch_op.drop_column('reasignado_en')
        batch_op.drop_column('motivo_reasignacion')
        batch_op.drop_column('reasignado_desde')
