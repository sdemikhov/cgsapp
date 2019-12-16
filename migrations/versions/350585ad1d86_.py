"""empty message

Revision ID: 350585ad1d86
Revises: 36dd7dc817cd
Create Date: 2019-12-15 04:45:09.116251

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '350585ad1d86'
down_revision = '36dd7dc817cd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('storage_for_make_config', sa.Column('hostname', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('storage_for_make_config', 'hostname')
    # ### end Alembic commands ###
