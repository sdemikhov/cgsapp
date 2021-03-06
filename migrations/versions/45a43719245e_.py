"""empty message

Revision ID: 45a43719245e
Revises: f3f507ca64d4
Create Date: 2019-12-15 10:27:02.436103

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45a43719245e'
down_revision = 'f3f507ca64d4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('storage_for_make_config', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.create_unique_constraint(None, 'storage_for_make_config', ['user_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'storage_for_make_config', type_='unique')
    op.alter_column('storage_for_make_config', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###
