"""Isolated temporary demo identities and a durable guest issuance budget."""
from alembic import op
import sqlalchemy as sa

revision = "f60100000001"
down_revision = "f50100000001"
branch_labels = depends_on = None


def upgrade():
    op.create_table("demo_sessions",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ip_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mutations", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_demo_sessions_ip_hash", "demo_sessions", ["ip_hash"])
    budget = op.create_table("demo_budget",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("day", sa.String(10), nullable=False),
        sa.Column("issued", sa.Integer(), nullable=False))
    op.bulk_insert(budget, [{"id": 1, "day": "1970-01-01", "issued": 0}])


def downgrade():
    raise RuntimeError("Review disposable session retention before downgrading")
