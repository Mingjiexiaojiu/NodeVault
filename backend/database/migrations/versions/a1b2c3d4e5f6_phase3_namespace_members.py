"""phase3_namespace_members

Revision ID: a1b2c3d4e5f6
Revises: c74a3f043f03
Create Date: 2026-03-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "c74a3f043f03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add description column to namespaces
    op.add_column("namespaces", sa.Column("description", sa.Text(), nullable=True))

    # 2. Create namespace_members table
    op.create_table(
        "namespace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("namespace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("namespaces.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("namespace_id", "user_id", name="uq_namespace_member"),
    )

    # 3. Migrate existing data: every namespace owner becomes admin member
    op.execute(
        """
        INSERT INTO namespace_members (id, namespace_id, user_id, role, joined_at)
        SELECT gen_random_uuid(), n.id, n.owner_id, 'admin', n.created_at
        FROM namespaces n
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("namespace_members")
    op.drop_column("namespaces", "description")
