"""User-reviewed learning captures and confirmed observations."""
from alembic import op
import sqlalchemy as sa

revision = "f20200000002"
down_revision = "f20100000001"
branch_labels = depends_on = None


def upgrade():
    op.create_table("learning_captures",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String, nullable=False),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("proposed_interpretation", sa.JSON),
        sa.Column("confirmed_interpretation", sa.JSON),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("processing_model", sa.String),
        sa.Column("extraction_version", sa.String),
        sa.Column("confirmation_digest", sa.String),
        sa.Column("study_log_id", sa.Integer, sa.ForeignKey("study_logs.id", ondelete="SET NULL")),
        sa.Column("learning_track_id", sa.Integer, sa.ForeignKey("learning_tracks.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("id", "user_id", name="uq_capture_owner"),
        sa.CheckConstraint("source_type IN ('text','voice')", name="ck_capture_source"),
        sa.CheckConstraint("status IN ('pending','failed','confirmed','discarded')", name="ck_capture_status"),
        sa.CheckConstraint("version > 0", name="ck_capture_version"))
    op.create_index("ix_learning_captures_user_id", "learning_captures", ["user_id"])
    op.create_table("learning_observations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("capture_id", sa.Integer, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("observation_type", sa.String, nullable=False),
        sa.Column("topic", sa.String, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("evidence", sa.Text, nullable=False),
        sa.Column("provenance", sa.String, nullable=False),
        sa.Column("memory_id", sa.Integer, sa.ForeignKey("memories.id", ondelete="SET NULL"), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["capture_id", "user_id"], ["learning_captures.id", "learning_captures.user_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("capture_id", "position", name="uq_capture_observation_position"),
        sa.CheckConstraint("observation_type IN ('learned','understood_self_report','difficulty','open_question','intended_next_step')", name="ck_observation_type"),
        sa.CheckConstraint("provenance = 'user_confirmed'", name="ck_observation_provenance"),
        sa.CheckConstraint("position >= 0", name="ck_observation_position"))
    op.create_index("ix_learning_observations_user_id", "learning_observations", ["user_id"])
    op.create_index("ix_learning_observations_capture_id", "learning_observations", ["capture_id"])


def downgrade():
    raise RuntimeError("Capture retention requires a reviewed manual downgrade")
