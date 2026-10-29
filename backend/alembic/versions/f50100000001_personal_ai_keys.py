"""Encrypted user-owned Gemini credentials. No existing records are rewritten."""
from alembic import op
import sqlalchemy as sa

revision = "f50100000001"
down_revision = "f40100000001"
branch_labels = depends_on = None


def upgrade():
    op.create_table("ai_credentials",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("encrypted_key", sa.Text(), nullable=False))


def downgrade():
    raise RuntimeError("Review encrypted credential retention before downgrading")
