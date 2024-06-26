"""migrations-0.0.3-rc2

Revision ID: fbf94c515e04
Revises: 64a6f5fbfc82
Create Date: 2024-04-22 19:47:19.139869

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fbf94c515e04"
down_revision: Union[str, None] = "64a6f5fbfc82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Upgrade the document_status type
    op.execute("ALTER TYPE datasource_type ADD VALUE IF NOT EXISTS 'S3';")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Downgrade the document_type type is intentionally ignored because existing records might already depend on it
    pass
    # ### end Alembic commands ###
