"""Preserve original action payload identity across status updates."""
from alembic import op
import sqlalchemy as sa
revision = "f40100000001"
down_revision = "f30100000001"
branch_labels = depends_on = None


def upgrade():
    op.add_column("learning_actions", sa.Column("request_digest", sa.String(64), nullable=True))


def downgrade():
    raise RuntimeError("Review action idempotency retention before downgrading")
