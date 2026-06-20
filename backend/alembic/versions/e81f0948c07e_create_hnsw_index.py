"""create_hnsw_index

Revision ID: e81f0948c07e
Revises: c08a51cd4965
Create Date: 2026-06-19

"""

from typing import Sequence, Union
from alembic import op

revision: str = "e81f0948c07e"
down_revision: Union[str, Sequence[str], None] = "c08a51cd4965"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS
        memory_embeddings_hnsw_idx
        ON memory_embeddings
        USING hnsw
        (embedding vector_cosine_ops)
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS
        memory_embeddings_hnsw_idx
    """)