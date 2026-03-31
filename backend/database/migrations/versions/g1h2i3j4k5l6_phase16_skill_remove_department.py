"""Phase 16: Remove department_id from skills table.

Skills are no longer scoped to departments.
Name uniqueness is now global instead of per-department.

Revision ID: g1h2i3j4k5l6
Revises: b5c6d7e8f9a0
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "g1h2i3j4k5l6"
down_revision = "b5c6d7e8f9a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old unique constraint (name + department_id)
    op.drop_constraint("uq_skill_name_department", "skills", type_="unique")

    # Drop FK and column
    op.drop_constraint("skills_department_id_fkey", "skills", type_="foreignkey")
    op.drop_column("skills", "department_id")

    # Add new global unique constraint on name only
    op.create_unique_constraint("uq_skill_name", "skills", ["name"])


def downgrade() -> None:
    op.drop_constraint("uq_skill_name", "skills", type_="unique")
    op.add_column("skills", sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "skills_department_id_fkey", "skills", "departments",
        ["department_id"], ["id"], ondelete="CASCADE"
    )
    op.create_unique_constraint("uq_skill_name_department", "skills", ["name", "department_id"])
