"""Learning action records and continuity feedback."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f30100000001"
down_revision = "f20200000002"
branch_labels = depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "learning_actions" not in tables:
        op.create_table(
            "learning_actions",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("action_type", sa.String(64), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("observation_id", sa.Integer, sa.ForeignKey("learning_observations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("capture_id", sa.Integer, sa.ForeignKey("learning_captures.id", ondelete="SET NULL"), nullable=True),
            sa.Column("learning_track_id", sa.Integer, sa.ForeignKey("learning_tracks.id", ondelete="SET NULL"), nullable=True),
            sa.Column("topic", sa.String(255), nullable=True),
            sa.Column("recommendation_id", sa.String(255), nullable=True),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "idempotency_key", name="uq_learning_action_user_idempotency"),
            sa.CheckConstraint("status IN ('completed','resolved','dismissed')", name="ck_learning_action_status"),
            sa.CheckConstraint("action_type IN ('next_step','difficulty','question','review','recommendation')", name="ck_learning_action_type"),
        )
        op.create_index("ix_learning_actions_user_id", "learning_actions", ["user_id"])
        op.create_index("ix_learning_actions_observation_id", "learning_actions", ["observation_id"])
        op.create_index("ix_learning_actions_topic", "learning_actions", ["topic"])
        op.create_index("ix_learning_actions_recommendation_id", "learning_actions", ["recommendation_id"])


def downgrade():
    raise RuntimeError("Learning action retention requires a reviewed manual downgrade")
