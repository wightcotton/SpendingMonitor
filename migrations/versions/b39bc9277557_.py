"""empty message

Revision ID: b39bc9277557
Revises: cb64165d04da
Create Date: 2020-08-05 11:11:23.143284

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b39bc9277557'
down_revision = 'cb64165d04da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('_user_state_uc', 'state_lookup', ['user_id', 'state'])
    op.drop_index('ix_state_lookup_state', table_name='state_lookup')
    op.create_index(op.f('ix_state_lookup_state'), 'state_lookup', ['state'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_state_lookup_state'), table_name='state_lookup')
    op.create_index('ix_state_lookup_state', 'state_lookup', ['state'], unique=True)
    op.drop_constraint('_user_state_uc', 'state_lookup', type_='unique')
    # ### end Alembic commands ###
