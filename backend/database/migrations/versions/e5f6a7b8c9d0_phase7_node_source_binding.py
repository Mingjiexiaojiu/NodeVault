"""phase7_node_source_binding

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-21 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source_credential_id column with FK
    op.add_column(
        "nodes",
        sa.Column(
            "source_credential_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("service_credentials.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    # Add source_path column
    op.add_column(
        "nodes",
        sa.Column("source_path", sa.String(512), nullable=True),
    )
    # Index for filtering nodes by their source service
    op.create_index(
        "ix_nodes_source_credential_id",
        "nodes",
        ["source_credential_id"],
    )

    # Backfill source_credential_id from node_versions.runtime_config JSONB
    # Sets source_credential_id on nodes whose default version has a credential_id
    op.execute(
        """
        UPDATE nodes n
        SET source_credential_id = (
            SELECT CAST(nv.runtime_config->>'credential_id' AS UUID)
            FROM node_versions nv
            WHERE nv.node_id = n.id
              AND nv.is_default = TRUE
              AND nv.runtime_config->>'credential_id' IS NOT NULL
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM node_versions nv
            WHERE nv.node_id = n.id
              AND nv.is_default = TRUE
              AND nv.runtime_config->>'credential_id' IS NOT NULL
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_nodes_source_credential_id", table_name="nodes")
    op.drop_column("nodes", "source_path")
    op.drop_column("nodes", "source_credential_id")
