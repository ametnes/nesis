"""add tasks to role_action_resource_type

Revision ID: 50bebf15de30
Revises: 3d6d802ca102
Create Date: 2024-06-13 23:41:54.517558

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "50bebf15de30"
down_revision: Union[str, None] = "3d6d802ca102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TYPE role_action_resource_type ADD VALUE IF NOT EXISTS 'APPS';")
    op.execute("ALTER TYPE role_action_resource_type ADD VALUE IF NOT EXISTS 'TASKS';")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    """
    We keep the APPS and TASKS types as might be used by the application
    """
    pass
    # ### end Alembic commands ###
