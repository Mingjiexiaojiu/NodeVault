"""phase6_service_credentials

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-20 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("base_url", sa.String(2048), nullable=False),
        sa.Column("auth_type", sa.String(32), nullable=False),
        # bearer_login
        sa.Column("login_endpoint", sa.String(2048), nullable=True),
        sa.Column("login_method", sa.String(8), nullable=True, server_default="POST"),
        sa.Column("login_body_template", sa.Text(), nullable=True),
        sa.Column("credential_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("credential_nonce", sa.LargeBinary(), nullable=True),
        sa.Column("token_json_path", sa.String(256), nullable=True),
        sa.Column("token_ttl", sa.Integer(), nullable=True),
        # bearer_static
        sa.Column("static_token_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("static_token_nonce", sa.LargeBinary(), nullable=True),
        # api_key
        sa.Column(
            "api_key_header", sa.String(128), nullable=True, server_default="X-API-Key"
        ),
        sa.Column("api_key_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("api_key_nonce", sa.LargeBinary(), nullable=True),
        # timestamps
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "credential_token_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "credential_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("service_credentials.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("credential_token_cache")
    op.drop_table("service_credentials")
