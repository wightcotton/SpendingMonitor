"""empty message

Revision ID: cb64165d04da
Revises: 7b4ffcb858a8
Create Date: 2020-06-06 14:32:52.715691

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb64165d04da'
down_revision = '7b4ffcb858a8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('category_state', sa.Column('comment', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('category_state', 'comment')
    # ### end Alembic commands ###