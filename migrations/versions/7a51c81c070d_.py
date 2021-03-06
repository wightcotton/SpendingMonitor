"""empty message

Revision ID: 7a51c81c070d
Revises: 3ba3c0544de4
Create Date: 2020-05-01 11:47:54.772108

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a51c81c070d'
down_revision = '3ba3c0544de4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('uploaded_file', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'uploaded_file', 'user', ['user_id'], ['id'])
    op.add_column('user', sa.Column('recent_file_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'uploaded_file', ['recent_file_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'recent_file_id')
    op.drop_constraint(None, 'uploaded_file', type_='foreignkey')
    op.drop_column('uploaded_file', 'user_id')
    # ### end Alembic commands ###
