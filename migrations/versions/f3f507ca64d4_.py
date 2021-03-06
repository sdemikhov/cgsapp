"""empty message

Revision ID: f3f507ca64d4
Revises: 350585ad1d86
Create Date: 2019-12-15 05:01:13.563451

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3f507ca64d4'
down_revision = '350585ad1d86'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('storage_for_make_config', sa.Column('client_ports', sa.String(length=64), nullable=True))
    op.drop_column('storage_for_make_config', 'pppoe_ports')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('storage_for_make_config', sa.Column('pppoe_ports', sa.VARCHAR(length=64), nullable=True))
    op.drop_column('storage_for_make_config', 'client_ports')
    # ### end Alembic commands ###
