"""add transaction model

Revision ID: f169eaf82ec6
Revises: 03464fed874b
Create Date: 2023-07-06 06:14:43.409175

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'f169eaf82ec6'
down_revision = '03464fed874b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('transaction',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('createdAt', sa.Integer(), nullable=False),
    sa.Column('dirName', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('v', sa.Integer(), nullable=True),
    sa.Column('trader_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['trader_id'], ['trader.id'], name=op.f('fk_transaction_trader_id_trader')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_transaction'))
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transaction')
    # ### end Alembic commands ###