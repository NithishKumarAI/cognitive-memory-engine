"""Represent previously manually provisioned tables without replacing them."""
from alembic import op
import sqlalchemy as sa

revision = "f20100000001"
down_revision = "903ce59b718d"
branch_labels = depends_on = None


def upgrade():
    schema = op.get_bind().execute(sa.text("SELECT current_schema()")).scalar_one()
    inspector = sa.inspect(op.get_bind())
    definitions = {
        "conversations": [sa.Column("message", sa.Text, nullable=False), sa.Column("response", sa.Text, nullable=False)],
        "usage_limits": [sa.Column("daily_requests", sa.Integer, nullable=False), sa.Column("monthly_requests", sa.Integer, nullable=False)],
    }
    for name, columns in definitions.items():
        if inspector.has_table(name, schema=schema):
            required = {"id", "user_id", "created_at", *(c.name for c in columns)}
            if not required.issubset({c["name"] for c in inspector.get_columns(name, schema=schema)}):
                raise RuntimeError("Existing baseline table requires explicit reconciliation")
            continue
        op.create_table(name,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, unique=name == "usage_limits"),
            *columns,
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
        op.create_index(f"ix_{name}_id", name, ["id"])


def downgrade():
    raise RuntimeError("Baseline reconciliation requires a reviewed manual downgrade")
