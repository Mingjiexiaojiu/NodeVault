"""phase12_db_integrity_security_fixes

- Fix: user_ai_configs.api_key → encrypted storage (api_key_encrypted + api_key_nonce)
- Fix: Add Partial Unique Index on node_versions(node_id) WHERE is_default=true
- Fix: Add Partial Unique Index on skill_versions(skill_id) WHERE is_default=true
- Fix: discovery_sessions.base_url DROP DEFAULT, ALTER COLUMN nullable

Revision ID: c1d2e3f4a5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-03-23 12:00:00.000000

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_encrypt_key() -> None:
    """Ensure CREDENTIAL_ENCRYPT_KEY is set before data migration."""
    if not os.environ.get("CREDENTIAL_ENCRYPT_KEY"):
        raise RuntimeError(
            "CREDENTIAL_ENCRYPT_KEY environment variable is not set. "
            "Cannot encrypt user_ai_configs.api_key. "
            "Please set it before running this migration."
        )


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. discovery_sessions.base_url: DROP DEFAULT, ALTER COLUMN nullable
    # ------------------------------------------------------------------
    op.alter_column(
        "discovery_sessions",
        "base_url",
        existing_type=sa.String(2048),
        nullable=True,
        server_default=None,
    )

    # ------------------------------------------------------------------
    # 2. Fix duplicate is_default=true in node_versions (keep latest)
    # ------------------------------------------------------------------
    conn.execute(sa.text("""
        UPDATE node_versions nv
        SET is_default = false
        WHERE is_default = true
          AND id NOT IN (
              SELECT DISTINCT ON (node_id) id
              FROM node_versions
              WHERE is_default = true
              ORDER BY node_id, created_at DESC
          )
    """))

    # ------------------------------------------------------------------
    # 3. Fix duplicate is_default=true in skill_versions (keep latest)
    # ------------------------------------------------------------------
    conn.execute(sa.text("""
        UPDATE skill_versions sv
        SET is_default = false
        WHERE is_default = true
          AND id NOT IN (
              SELECT DISTINCT ON (skill_id) id
              FROM skill_versions
              WHERE is_default = true
              ORDER BY skill_id, created_at DESC
          )
    """))

    # ------------------------------------------------------------------
    # 4. Create Partial Unique Indexes for is_default
    # ------------------------------------------------------------------
    op.create_index(
        "uq_node_default_version",
        "node_versions",
        ["node_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )
    op.create_index(
        "uq_skill_default_version",
        "skill_versions",
        ["skill_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )

    # ------------------------------------------------------------------
    # 5. user_ai_configs: ADD api_key_encrypted + api_key_nonce columns
    # ------------------------------------------------------------------
    op.add_column(
        "user_ai_configs",
        sa.Column("api_key_encrypted", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "user_ai_configs",
        sa.Column("api_key_nonce", sa.LargeBinary(), nullable=True),
    )

    # ------------------------------------------------------------------
    # 6. Data migration: encrypt existing api_key values
    # ------------------------------------------------------------------
    _get_encrypt_key()

    # Import here to ensure the env var check above runs first
    from backend.core.credential_vault import encrypt_value

    rows = conn.execute(
        sa.text("SELECT id, api_key FROM user_ai_configs WHERE api_key IS NOT NULL")
    ).fetchall()

    for row in rows:
        row_id, api_key = row
        if api_key:
            ciphertext, nonce = encrypt_value(api_key)
            conn.execute(
                sa.text(
                    "UPDATE user_ai_configs "
                    "SET api_key_encrypted = :enc, api_key_nonce = :nonce "
                    "WHERE id = :id"
                ),
                {"enc": ciphertext, "nonce": nonce, "id": row_id},
            )

    # ------------------------------------------------------------------
    # 7. Make encrypted columns NOT NULL, then DROP plain api_key
    # ------------------------------------------------------------------
    op.alter_column("user_ai_configs", "api_key_encrypted", nullable=False)
    op.alter_column("user_ai_configs", "api_key_nonce", nullable=False)
    op.drop_column("user_ai_configs", "api_key")


def downgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # Reverse 7: ADD api_key column back (nullable first)
    # ------------------------------------------------------------------
    op.add_column(
        "user_ai_configs",
        sa.Column("api_key", sa.Text(), nullable=True),
    )

    # ------------------------------------------------------------------
    # Reverse 6: Decrypt and restore api_key
    # ------------------------------------------------------------------
    _get_encrypt_key()

    from backend.core.credential_vault import decrypt_value

    rows = conn.execute(
        sa.text(
            "SELECT id, api_key_encrypted, api_key_nonce FROM user_ai_configs "
            "WHERE api_key_encrypted IS NOT NULL"
        )
    ).fetchall()

    for row in rows:
        row_id, ciphertext, nonce = row
        if ciphertext and nonce:
            plaintext = decrypt_value(bytes(ciphertext), bytes(nonce))
            conn.execute(
                sa.text("UPDATE user_ai_configs SET api_key = :key WHERE id = :id"),
                {"key": plaintext, "id": row_id},
            )

    # Make api_key NOT NULL after restoring data
    op.alter_column("user_ai_configs", "api_key", nullable=False)

    # ------------------------------------------------------------------
    # Reverse 5: DROP encrypted columns
    # ------------------------------------------------------------------
    op.drop_column("user_ai_configs", "api_key_nonce")
    op.drop_column("user_ai_configs", "api_key_encrypted")

    # ------------------------------------------------------------------
    # Reverse 4: DROP Partial Unique Indexes
    # ------------------------------------------------------------------
    op.drop_index("uq_node_default_version", table_name="node_versions")
    op.drop_index("uq_skill_default_version", table_name="skill_versions")

    # ------------------------------------------------------------------
    # Reverse 1: Restore discovery_sessions.base_url NOT NULL with default ''
    # ------------------------------------------------------------------
    # Fill NULLs before restoring NOT NULL constraint
    conn.execute(
        sa.text("UPDATE discovery_sessions SET base_url = '' WHERE base_url IS NULL")
    )
    op.alter_column(
        "discovery_sessions",
        "base_url",
        existing_type=sa.String(2048),
        nullable=False,
        server_default="",
    )
