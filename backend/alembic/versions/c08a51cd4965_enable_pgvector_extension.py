"""enable_pgvector_extension

Revision ID: c08a51cd4965
Revises: 86a536d3ece5
Create Date: 2026-06-19

"""

from typing import Sequence, Union
from alembic import op

revision: str = "c08a51cd4965"
down_revision: Union[str, Sequence[str], None] = "86a536d3ece5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )


def downgrade() -> None:
    op.execute(
        "DROP EXTENSION IF EXISTS vector"
    )