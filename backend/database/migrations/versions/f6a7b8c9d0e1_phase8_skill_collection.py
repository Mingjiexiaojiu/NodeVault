"""phase8_skill_collection

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-22 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create skills table
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "namespace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("namespaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("is_stale", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("name", "namespace_id", name="uq_skill_name_namespace"),
    )
    op.create_index("ix_skills_name", "skills", ["name"])
    op.create_index("ix_skills_status", "skills", ["status"])
    op.create_index("ix_skills_namespace_id", "skills", ["namespace_id"])

    # Create skill_versions table
    op.create_table(
        "skill_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("skill_md", sa.Text, nullable=False),
        sa.Column("node_snapshot", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("release_notes", sa.Text, nullable=True),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("skill_id", "version", name="uq_skill_version"),
    )
    op.create_index("ix_skill_versions_skill_id", "skill_versions", ["skill_id"])

    # Add skill_id FK and usage_hint to nodes table
    op.add_column(
        "nodes",
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "nodes",
        sa.Column("usage_hint", sa.String(500), nullable=True),
    )
    op.create_index("ix_nodes_skill_id", "nodes", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_nodes_skill_id", "nodes")
    op.drop_column("nodes", "usage_hint")
    op.drop_column("nodes", "skill_id")
    op.drop_index("ix_skill_versions_skill_id", "skill_versions")
    op.drop_table("skill_versions")
    op.drop_index("ix_skills_namespace_id", "skills")
    op.drop_index("ix_skills_status", "skills")
    op.drop_index("ix_skills_name", "skills")
    op.drop_table("skills")
