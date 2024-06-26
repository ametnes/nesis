"""migrations-0.0.3-rc1

Revision ID: 64a6f5fbfc82
Revises: 953b4d309aaa
Create Date: 2024-04-18 23:01:27.466829

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "64a6f5fbfc82"
down_revision: Union[str, None] = "953b4d309aaa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "task",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("uuid", sa.Unicode(length=255), nullable=False),
        sa.Column(
            "type", sa.Enum("INGEST_DATASOURCE", name="task_type"), nullable=False
        ),
        sa.Column("schedule", sa.Unicode(length=255), nullable=False),
        sa.Column("parent_id", sa.Unicode(length=255), nullable=True),
        sa.Column(
            "definition", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "RUNNING", "PAUSED", "COMPLETED", "ERROR", "CREATED", name="task_status"
            ),
            nullable=False,
        ),
        sa.Column("create_date", sa.DateTime(), nullable=False),
        sa.Column("update_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type", "schedule", name="uq_task_type_schedule"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("idx_task_parent", "task", ["parent_id"], unique=False)
    op.create_index("idx_task_type", "task", ["type"], unique=False)
    # ### end Alembic commands ###

    # Upgrade the document_status type
    op.execute("ALTER TYPE datasource_status ADD VALUE IF NOT EXISTS 'INGESTING';")


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_task_type", table_name="task")
    op.drop_index("idx_task_parent", table_name="task")
    op.drop_table("task")
    # ### end Alembic commands ###

    # Downgrade the document_status type is intentionally ignored because existing records might already depend on it
