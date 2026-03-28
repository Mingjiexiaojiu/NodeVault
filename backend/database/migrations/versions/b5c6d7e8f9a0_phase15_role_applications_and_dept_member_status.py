"""phase15_role_applications_and_dept_member_status

- Create table: role_applications
- Add column: department_members.status

Revision ID: b5c6d7e8f9a0
Revises: a2b3c4d5e6f7
Create Date: 2026-03-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b5c6d7e8f9a0"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 新建 role_applications 表
    op.create_table(
        "role_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_role", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_role_applications_user_id", "role_applications", ["user_id"])
    op.create_index("ix_role_applications_status", "role_applications", ["status"])

    # 2. 为 department_members 新增 status 字段
    op.add_column(
        "department_members",
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
    )
    op.create_index("ix_department_members_status", "department_members", ["status"])


def downgrade() -> None:
    op.drop_index("ix_department_members_status", table_name="department_members")
    op.drop_column("department_members", "status")

    op.drop_index("ix_role_applications_status", table_name="role_applications")
    op.drop_index("ix_role_applications_user_id", table_name="role_applications")
    op.drop_table("role_applications")
