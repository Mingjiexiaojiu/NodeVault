"""phase4_user_role_and_profile

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 身份字段：0=超级管理员, 1=主管, 2=普通用户
    op.add_column("users", sa.Column("role", sa.Integer(), nullable=False, server_default="2"))
    # 个人资料字段
    op.add_column("users", sa.Column("display_name", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(512), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("department", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("title", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "title")
    op.drop_column("users", "department")
    op.drop_column("users", "phone")
    op.drop_column("users", "bio")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "display_name")
    op.drop_column("users", "role")
