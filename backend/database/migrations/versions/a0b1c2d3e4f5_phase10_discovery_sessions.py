"""phase10_discovery_sessions

Revision ID: a0b1c2d3e4f5
Revises: f6a7b8c9d0e1
Create Date: 2026-03-19 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create discovery_sessions table
    op.create_table(
        "discovery_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("base_url", sa.String(2048), nullable=False, server_default=""),
        sa.Column("source", sa.String(16), nullable=False, server_default="probe"),
        sa.Column("status", sa.String(16), nullable=False, server_default="probing"),
        sa.Column("spec_url", sa.String(2048), nullable=True),
        sa.Column("total_operations", sa.Integer, nullable=True),
        sa.Column("imported_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_discovery_sessions_user_id", "discovery_sessions", ["user_id"])
    op.create_index("ix_discovery_sessions_status", "discovery_sessions", ["status"])

    # Add discovery_session_id to nodes
    op.add_column(
        "nodes",
        sa.Column(
            "discovery_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_nodes_discovery_session_id", "nodes", ["discovery_session_id"])


def downgrade() -> None:
    op.drop_index("ix_nodes_discovery_session_id", table_name="nodes")
    op.drop_column("nodes", "discovery_session_id")
    op.drop_index("ix_discovery_sessions_status", table_name="discovery_sessions")
    op.drop_index("ix_discovery_sessions_user_id", table_name="discovery_sessions")
    op.drop_table("discovery_sessions")
