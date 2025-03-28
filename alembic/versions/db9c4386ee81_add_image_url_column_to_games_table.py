"""Add image_url column to games table

Revision ID: db9c4386ee81
Revises: 3e71aaeb39f1
Create Date: 2025-03-24 13:53:21.403934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db9c4386ee81'
down_revision: Union[str, None] = '3e71aaeb39f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('games', sa.Column('image_url', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('games', 'image_url')
    # ### end Alembic commands ###
