"""empty message

Revision ID: 7b4ffcb858a8
Revises: d6bd9df7f53d
Create Date: 2020-06-06 13:21:15.310795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b4ffcb858a8'
down_revision = 'd6bd9df7f53d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category_state',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(length=64), nullable=True),
    sa.Column('state', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['state'], ['state_lookup.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_category_state_category'), 'category_state', ['category'], unique=False)
    op.create_index(op.f('ix_category_state_timestamp'), 'category_state', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_category_state_timestamp'), table_name='category_state')
    op.drop_index(op.f('ix_category_state_category'), table_name='category_state')
    op.drop_table('category_state')
    # ### end Alembic commands ###
